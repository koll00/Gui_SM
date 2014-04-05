import sys, os
sys.path.append('..' + os.path.sep)
import os.path as osp
import atexit
import socket
import shutil
import threading
import errno

# Test if IPython v0.13+ is installed to eventually switch to PyQt API #2
from SMlib.utils.programs import is_module_installed
from SMlib.config import CONF, EDIT_EXT, OPEN_FILES_PORT, IMPORT_EXT
from SMlib.configs.baseconfig import (_,STDOUT, STDERR)
from SMlib.configs.ipythonconfig import IPYTHON_QT_MODULE, SUPPORTED_IPYTHON
from SMlib import dependencies
from SMlib.utils import module_completion
from SMlib.utils.misc import select_port

dependencies.add("IPython", _("IPython Console integration"),
                 required_version=SUPPORTED_IPYTHON)

if is_module_installed(IPYTHON_QT_MODULE, SUPPORTED_IPYTHON):
    # Importing IPython will eventually set the QT_API environment variable
    import IPython  # analysis:ignore
    if os.environ.get('QT_API', 'pyqt') == 'pyqt':
        # If PyQt is the selected GUI toolkit (at this stage, only the
        # bootstrap script has eventually set this option), switch to 
        # PyQt API #2 by simply importing the IPython qt module
        os.environ['QT_API'] = 'pyqt'
        try:
            from IPython.external import qt  #analysis:ignore
        except ImportError:
            # Avoid raising any error here: the SMlib.requirements module
            # will take care of it, in a user-friendly way (Tkinter message box
            # if no GUI toolkit is installed)
            pass


from SMlib.plugins.ipythonConsole import IPythonConsole
from SMlib.plugins.externalconsole import ExternalConsole
from SMlib.plugins.editor import Editor
from SMlib.plugins.console import Console
from SMlib.plugins.workingdirectory import WorkingDirectory
from SMlib.plugins.variableexplorer import VariableExplorer
from SMlib.plugins.inspector import ObjectInspector
from SMlib.plugins.findinfiles import FindInFiles
from SMlib.plugins.history import HistoryLog
from SMlib.plugins.configdialog import (ConfigDialog, MainConfigPage,
                                            ColorSchemeConfigPage)
from SMlib.plugins.shortcuts import ShortcutsConfigPage
from SMlib.plugins.runconfig import RunConfigPage
from SMlib.plugins.projectexplorer import ProjectExplorer
from SMlib.plugins.explorer import Explorer

from SMlib.widgets.pathmanager import PathManager

from PyQt4.QtGui import (QMainWindow, QApplication, QAction,QDockWidget, 
                        QShortcut, QMenu, QMessageBox, QColor)

from PyQt4.Qt import QKeySequence
from PyQt4.QtCore import SIGNAL, Qt, QSize, QPoint,QByteArray

from SMlib.widgets.status import MemoryStatus, CPUStatus
from SMlib.configs.baseconfig import debug_print, _, TEST, get_conf_path
from SMlib.configs.userconfig import NoDefault 
from SMlib.configs.guiconfig import get_shortcut, remove_deprecated_shortcuts
from SMlib.py3compat import qbytearray_to_str
from SMlib.configs.baseconfig import debug_print
from SMlib.utils.qthelpers import (create_action, add_actions, get_icon,
                                       get_std_icon, add_shortcut_to_tooltip,
                                       create_module_bookmark_actions,
                                       create_bookmark_action,
                                       create_program_action, DialogManager,
                                       keybinding, qapplication,
                                       create_python_script_action, file_uri, from_qvariant)
from SMlib.utils import encoding, programs
#from SMlib.otherplugins import get_spyderplugins_mods

# Get the cwd before initializing WorkingDirectory, which sets it to the one
# used in the last session
CWD = os.getcwd()

class MainWindow(QMainWindow):
    SM_path = get_conf_path('.path')
    DOCKOPTIONS = QMainWindow.AllowTabbedDocks|QMainWindow.AllowNestedDocks
    
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        
        qapp = QApplication.instance()
        self.default_style = str(qapp.style().objectName())
        
        self.light = False
        self.new_instance = False
        self.profile = False
        self.multithreaded = False
        self.init_workdir = None
        # Shortcut management data
        self.shortcut_data = []
        
        # Loading SM path
        self.path = []
        self.project_path = []
        if osp.isfile(self.SM_path):
            self.path, _x = encoding.readlines(self.SM_path)
            self.path = [name for name in self.path if osp.isdir(name)]
        self.remove_path_from_sys_path()
        self.add_path_to_sys_path()
        
        
        self.console = None
        self.workingdirectory = None
        self.editor = None
        self.explorer = None
        self.inspector = None
        self.onlinehelp = None
        self.projectexplorer = None
        self.outlineexplorer = None
        self.historylog = None
        self.extconsole = None
        self.ipyconsole = None
        self.variableexplorer = None
        self.findinfiles = None
        self.thirdparty_plugins = None
        # Menu bars
        self.file_menu = None
        self.file_menu_actions = []
        self.edit_menu = None
        self.edit_menu_actions = []
        self.search_menu = None
        self.search_menu_actions = []
        self.source_menu = None
        self.source_menu_actions = []
        self.run_menu = None
        self.run_menu_actions = []
        self.debug_menu = None
        self.debug_menu_actions = []
        self.consoles_menu = None
        self.consoles_menu_actions = []
        self.tools_menu = None
        self.tools_menu_actions = []
        self.external_tools_menu = None
        
        # Toolbars
        self.main_toolbar = None
        self.main_toolbar_actions = []
        self.file_toolbar = None
        self.file_toolbar_actions = []
        self.edit_toolbar = None
        self.edit_toolbar_actions = []
        self.search_toolbar = None
        self.search_toolbar_actions = []
        self.source_toolbar = None
        self.source_toolbar_actions = []
        self.run_toolbar = None
        self.run_toolbar_actions = []
        self.debug_toolbar = None
        self.debug_toolbar_actions = []
        
        # Actions
        self.close_dockwidget_action = None
        self.find_action = None
        self.find_next_action = None
        self.find_previous_action = None
        self.replace_action = None
        self.undo_action = None
        self.redo_action = None
        self.copy_action = None
        self.cut_action = None
        self.paste_action = None
        self.delete_action = None
        self.selectall_action = None
        self.maximize_action = None
        self.fullscreen_action = None
        
        self.interact_menu = None
        self.interact_menu_actions = []
        
        self.external_tools_menu_actions = []
        self.view_menu = None
        self.windows_toolbars_menu = None
        self.help_menu = None
        self.help_menu_actions = []
        
        # Status bar widgets
        self.mem_status = None
        self.cpu_status = None
        
        # List of satellite widgets (registered in add_dockwidget):
        self.widgetlist = []
        
        # Flags used if closing() is called by the exit() shell command
        self.already_closed = False
        self.is_starting_up = True
        
        # Preferences
        self.general_prefs = [MainConfigPage, ShortcutsConfigPage,
                              ColorSchemeConfigPage, RunConfigPage]
        
        self.prefs_index = None
        self.prefs_dialog_size = None
        
        self.floating_dockwidgets = []
        self.window_size = None
        self.window_position = None
        self.state_before_maximizing = None
        self.current_quick_layout = None
        self.previous_layout_settings = None
        self.last_plugin = None
        self.fullscreen_flag = None  # isFullscreen does not work as expected
        # The following flag remember the maximized state even when 
        # the window is in fullscreen mode:
        self.maximized_flag = None
        
        
                # Track which console plugin type had last focus
        # True: Console plugin
        # False: IPython console plugin
        self.last_console_plugin_focus_was_python = True
        
         # Server to open external files on a single instance
        self.open_files_server = socket.socket(socket.AF_INET,
                                               socket.SOCK_STREAM,
                                               socket.IPPROTO_TCP)
        self.apply_settings()
        self.debug_print("End of MainWindow constructor")
       
    def debug_print(self, message):
        """Debug prints"""
        debug_print(message)
         
    def setUp(self):
        """Setup main window"""
        
        self.createActions()
        
        #self.initalStatus()
        
        namespace = None
        
        # Internal console plugin
        self.console = Console(self, namespace, exitfunc=self.closing,
                                 profile=self.profile,
                                 multithreaded=self.multithreaded,
                                 message='Inspect Spyder internals:\n'\
                                         '  spy.app, spy.window, dir(spy)')
        self.console.register_plugin()
        
        # Working directory plugin
        self.workingdirectory = WorkingDirectory(self, self.init_workdir)
        self.workingdirectory.register_plugin()
        
         # Object inspector plugin
        if CONF.get('inspector', 'enable'):
            #self.set_splash(_("Loading object inspector..."))
            self.inspector = ObjectInspector(self)
            self.inspector.register_plugin()
         
        # Editor plugin
#         self.set_splash(_("Loading editor..."))
        self.editor = Editor(self)
        self.editor.register_plugin()
            
        
        # Find in files
        if CONF.get('find_in_files', 'enable'):
            self.findinfiles = FindInFiles(self)
            self.findinfiles.register_plugin()
        
        # Explorer
        if CONF.get('explorer', 'enable'):
            #self.set_splash(_("Loading file explorer..."))
            self.explorer = Explorer(self)
            self.explorer.register_plugin()
        
        # History log widget
        #if CONF.get('historylog', 'enable'):
            #self.set_splash(_("Loading history plugin..."))
            #self.historylog = HistoryLog(self)
            #self.historylog.register_plugin()
                
        
        if CONF.get('project_explorer', 'enable'):
                #self.set_splash(_("Loading project explorer..."))
                self.projectexplorer = ProjectExplorer(self)
                self.projectexplorer.register_plugin()
        
        self.extconsole = ExternalConsole(self, light_mode=self.light)
        self.extconsole.register_plugin()
        
        # Namespace browser
        if not self.light:
            # In light mode, namespace browser is opened inside external console
            # Here, it is opened as an independent plugin, in its own dockwidget
            #self.set_splash(_("Loading namespace browser..."))
            self.variableexplorer = VariableExplorer(self)
            self.variableexplorer.register_plugin()
        
        
        
        
        if is_module_installed(IPYTHON_QT_MODULE, SUPPORTED_IPYTHON):
            self.ipyconsole = IPythonConsole(self)
            self.ipyconsole.register_plugin()
        
        
        nsb = self.variableexplorer.add_shellwidget(self.console.shell)
        self.connect(self.console.shell, SIGNAL('refresh()'),
                     nsb.refresh_table)
        nsb.auto_refresh_button.setEnabled(False)
        
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        

        # Status bar widgets
        self.mem_status = MemoryStatus(self, self.status)
        self.cpu_status = CPUStatus(self, self.status)
        self.apply_statusbar_settings()
        
        '''
        # Third-party plugins
        for mod in get_spyderplugins_mods(prefix='p_', extension='.py'):
            try:
                print "mod", mod
                plugin = mod.PLUGIN_CLASS(self)
                self.thirdparty_plugins.append(plugin)
                plugin.register_plugin()
            except AttributeError, error:
                print >>STDERR, "%s: %s" % (mod, str(error))
'''
        
        
        # Apply all defined shortcuts (plugins + 3rd-party plugins)
        self.apply_shortcuts()
        self.remove_deprecated_shortcuts()
        
        # Emitting the signal notifying plugins that main window menu and 
        # toolbar actions are all defined:
        self.emit(SIGNAL('all_actions_defined()'))
        
        # Window set-up
        self.debug_print("Setting up window...")
        self.setup_layout(default=False)
        
        #self.splash.hide()
        
        # Enabling tear off for all menus except help menu
        if CONF.get('main', 'tear_off_menus'):
            for child in self.menuBar().children():
                if isinstance(child, QMenu) and child != self.help_menu:
                    child.setTearOffEnabled(True)
        
        # Menu about to show
        for child in self.menuBar().children():
            if isinstance(child, QMenu):
                self.connect(child, SIGNAL("aboutToShow()"),
                             self.update_edit_menu)
        
        self.debug_print("*** End of MainWindow setup ***")
        self.is_starting_up = False
        
    def createActions(self):
#         self.newAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&New",
#                 self, shortcut=QtGui.QKeySequence.New,
#                 statusTip="Create a new file", triggered=self.newFile)
        # self.debug_print("  ..core action")
        self.close_dockwidget_action = create_action(self,
                                        _("Close current dockwidget"),
                                        triggered=self.close_current_dockwidget,
                                        context=Qt.ApplicationShortcut)
        self.register_shortcut(self.close_dockwidget_action,
                                   "_", "Close dockwidget", "Shift+Ctrl+F4")
            
        _text = _("&Find text")
        self.find_action = create_action(self, _text, icon='find.png',
                                             tip=_text, triggered=self.find,
                                             context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_action, "Editor",
                                   "Find text", "Ctrl+F")
        self.find_next_action = create_action(self, _("Find &next"),
                  icon='findnext.png', triggered=self.find_next,
                  context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_next_action, "Editor",
                                   "Find next", "F3")
        self.find_previous_action = create_action(self,
                        _("Find &previous"),
                        icon='findprevious.png', triggered=self.find_previous,
                        context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_previous_action, "Editor",
                                   "Find previous", "Shift+F3")
        _text = _("&Replace text")
        self.replace_action = create_action(self, _text, icon='replace.png',
                                            tip=_text, triggered=self.replace,
                                            context=Qt.WidgetShortcut)
        self.register_shortcut(self.replace_action, "Editor",
                                   "Replace text", "Ctrl+H")
        def create_edit_action(text, tr_text, icon_name):
            textseq = text.split(' ')
            method_name = textseq[0].lower()+"".join(textseq[1:])
            return create_action(self, tr_text,
                                     shortcut=keybinding(text.replace(' ', '')),
                                     icon=get_icon(icon_name),
                                     triggered=self.global_callback,
                                     data=method_name,
                                     context=Qt.WidgetShortcut)
        self.undo_action = create_edit_action("Undo", _("Undo"),
                                                  'undo.png')
        self.redo_action = create_edit_action("Redo", _("Redo"), 'redo.png')
        self.copy_action = create_edit_action("Copy", _("Copy"),
                                                  'editcopy.png')
        self.cut_action = create_edit_action("Cut", _("Cut"), 'editcut.png')
        self.paste_action = create_edit_action("Paste", _("Paste"),
                                                   'editpaste.png')
        self.delete_action = create_edit_action("Delete", _("Delete"),
                                                    'editdelete.png')
        self.selectall_action = create_edit_action("Select All",
                                                       _("Select All"),
                                                       'selectall.png')
        self.edit_menu_actions = [self.undo_action, self.redo_action,
                                      None, self.cut_action, self.copy_action,
                                      self.paste_action, self.delete_action,
                                      None, self.selectall_action]
        self.search_menu_actions = [self.find_action, self.find_next_action,
                                        self.find_previous_action,
                                        self.replace_action]
        self.search_toolbar_actions = [self.find_action,
                                           self.find_next_action,
                                           self.replace_action]
        
        # Maximize current plugin
        self.maximize_action = create_action(self, '',
                                            triggered=self.maximize_dockwidget)
        self.register_shortcut(self.maximize_action, "_",
                                   "Maximize dockwidget", "Ctrl+Alt+Shift+M")
        self.__update_maximize_action()
            
        # Fullscreen mode
        self.fullscreen_action = create_action(self,
                                            _("Fullscreen mode"),
                                            triggered=self.toggle_fullscreen)
        self.register_shortcut(self.fullscreen_action, "_",
                                   "Fullscreen mode", "F11")
        add_shortcut_to_tooltip(self.fullscreen_action, context="_",
                                    name="Fullscreen mode")
            
        # Main toolbar
        self.main_toolbar_actions = [self.maximize_action,self.fullscreen_action]
        # View menu
        self.windows_toolbars_menu = QMenu(_("Windows and toolbars"), self)
        self.connect(self.windows_toolbars_menu, SIGNAL("aboutToShow()"),self.update_windows_toolbars_menu)
        
        # Populating file menu entries
        quit_action = create_action(self, _("&Quit"),
                                        icon='exit.png', tip=_("Quit"),
                                        triggered=self.close)
        self.register_shortcut(quit_action, "_", "Quit", "Ctrl+Q")
        self.file_menu_actions += [quit_action]
        
        # Tools + External Tools
        prefs_action = create_action(self, _("Pre&ferences"),icon='configure.png',
                                     triggered=self.edit_preferences)
        self.register_shortcut(prefs_action, "_", "Preferences","Ctrl+Alt+Shift+P")
        add_shortcut_to_tooltip(prefs_action, context="_",name="Preferences")
        
        SMlib_path_action = create_action(self,
                                    _("PYTHONPATH manager"),
                                    None, 'pythonpath_mgr.png',
                                    triggered=self.path_manager_callback,
                                    tip=_("Python Path Manager"),
                                    menurole=QAction.ApplicationSpecificRole)
        
        self.tools_menu_actions = [prefs_action, SMlib_path_action]
        
    def createMenus(self):
        'initial the menus for system'
        # File menu
        self.file_menu = self.menuBar().addMenu(_("&File"))
        # Edit menu
        self.edit_menu = self.menuBar().addMenu(_("&Edit"))
        # search_menu
        self.search_menu = self.menuBar().addMenu(_("&Search"))
        # Run menu
        self.run_menu = self.menuBar().addMenu(_("&Run"))
        # Interact menu
        self.interact_menu = self.menuBar().addMenu(_("&Interpreters"))
        # Tools menu
        self.tools_menu = self.menuBar().addMenu(_("&Tools"))
        # View menu
        self.view_menu = self.menuBar().addMenu(_("&View"))
        # Help menu
        self.help_menu = self.menuBar().addMenu(_("&Help"))
        
        add_actions(self.file_menu, self.file_menu_actions)
        add_actions(self.edit_menu, self.edit_menu_actions)
        add_actions(self.search_menu, self.search_menu_actions)
        add_actions(self.interact_menu, self.interact_menu_actions)
        add_actions(self.run_menu, self.run_menu_actions)
        add_actions(self.tools_menu, self.tools_menu_actions)
        
        self.view_menu.addMenu(self.windows_toolbars_menu)
        
        add_actions(self.view_menu, (None, self.maximize_action,
                                         self.fullscreen_action, None,
                                         #reset_layout_action, quick_layout_menu,
                                         None, self.close_dockwidget_action))
        
    def createToolBars(self):
        'initial the tool bar'
        #main tool bar
        self.main_toolbar = self.create_toolbar(_("&Main_toolbar"), "main_toolbar")
        #file tool bar
        self.file_toolbar = self.create_toolbar(_("&File"), "file")
        #edit tool bar
        self.edit_toolbar = self.create_toolbar(_("&Edit"), "edit")
        #search tool bar
        self.search_toolbar = self.create_toolbar(_("Search toolbar"),"search_toolbar")
        # Run toolbar
        self.run_toolbar = self.create_toolbar(_("Run toolbar"), "run_toolbar")
        
        add_actions(self.main_toolbar, self.main_toolbar_actions)
        add_actions(self.file_toolbar, self.file_toolbar_actions)
        add_actions(self.edit_toolbar, self.edit_toolbar_actions)
        add_actions(self.search_toolbar, self.search_toolbar_actions)
        add_actions(self.run_toolbar, self.run_toolbar_actions)
        
    def createStatusBar(self):
        ''
        self.status = self.statusBar()
        self.status.setObjectName("StatusBar")
        self.status.showMessage("Ready", 5000)
    
    #---- Window setup
    def create_toolbar(self, title, object_name, iconsize=24):
        """Create and return toolbar with *title* and *object_name*"""
        toolbar = self.addToolBar(title)
        toolbar.setObjectName(object_name)
        toolbar.setIconSize(QSize(iconsize, iconsize))
        return toolbar
      
    def update_windows_toolbars_menu(self):
        """Update windows&toolbars menu"""
        self.windows_toolbars_menu.clear()
        popmenu = self.createPopupMenu()
        add_actions(self.windows_toolbars_menu, popmenu.actions())
        
    def set_splash(self, message):
        """Set splash message"""
        if message:
            self.debug_print(message)
        self.splash.show()
        self.splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.white))
        QApplication.processEvents()
        
    def closeEvent(self, event):
        """closeEvent reimplementation"""
        if self.closing(True):
            event.accept()
        else:
            event.ignore()
            
    def closing(self, cancelable=False):
        """Exit tasks"""
#         if self.already_closed or self.is_starting_up:
#             return True
        prefix = 'window' + '/'
        self.save_current_window_settings(prefix)
        for widget in self.widgetlist:
            if not widget.closing_plugin(cancelable):
                return False
        #self.dialog_manager.close_all()
        self.already_closed = True
#        if CONF.get('main', 'single_instance'):
#            self.open_files_server.close()
        return True
    def add_dockwidget(self, child):
        """Add QDockWidget and toggleViewAction"""
        dockwidget, location = child.create_dockwidget()
        if CONF.get('main', 'vertical_dockwidget_titlebars'):
            dockwidget.setFeatures(dockwidget.features()|
                                   QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(location, dockwidget)
        self.widgetlist.append(child)

    def close_current_dockwidget(self):
        widget = QApplication.focusWidget()
        for plugin in self.widgetlist:
            if plugin.isAncestorOf(widget):
                plugin.dockwidget.hide()
                break
    
    def plugin_focus_changed(self):
        """Focus has changed from one plugin to another"""
        if self.light:
            #  There is currently no point doing the following in light mode
            return
        self.update_edit_menu()
        self.update_search_menu()
        
        # Now deal with Python shell and IPython plugins 
        shell = get_focus_python_shell()
        if shell is not None:
            # A Python shell widget has focus
            self.last_console_plugin_focus_was_python = True
            if self.inspector is not None:
                #  The object inspector may be disabled in .spyder.ini
                self.inspector.set_shell(shell)
            from SMlib.widgets.externalshell import pythonshell
            if isinstance(shell, pythonshell.ExtPythonShellWidget):
                shell = shell.parent()
            self.variableexplorer.set_shellwidget_from_id(id(shell))
        elif self.ipyconsole is not None:
            focus_client = self.ipyconsole.get_focus_client()
            if focus_client is not None:
                self.last_console_plugin_focus_was_python = False
                kwid = focus_client.kernel_widget_id
                if kwid is not None:
                    idx = self.extconsole.get_shell_index_from_id(kwid)
                    if idx is not None:
                        kw = self.extconsole.shellwidgets[idx]
                        if self.inspector is not None:
                            self.inspector.set_shell(kw)
                        self.variableexplorer.set_shellwidget_from_id(kwid)
                        # Setting the kernel widget as current widget for the 
                        # external console's tabwidget: this is necessary for
                        # the editor/console link to be working (otherwise,
                        # features like "Execute in current interpreter" will 
                        # not work with IPython clients unless the associated
                        # IPython kernel has been selected in the external 
                        # console... that's not brilliant, but it works for 
                        # now: we shall take action on this later
                        self.extconsole.tabwidget.setCurrentWidget(kw)
                        focus_client.get_control().setFocus()
                        
            
    def maximize_dockwidget(self, restore=False):
        """Shortcut: Ctrl+Alt+Shift+M
        First call: maximize current dockwidget
        Second call (or restore=True): restore original window layout"""
        if self.state_before_maximizing is None:
            if restore:
                return
            # No plugin is currently maximized: maximizing focus plugin
            self.state_before_maximizing = self.saveState()
            focus_widget = QApplication.focusWidget()
            for plugin in self.widgetlist:
                plugin.dockwidget.hide()
                if plugin.isAncestorOf(focus_widget):
                    self.last_plugin = plugin
            self.last_plugin.dockwidget.toggleViewAction().setDisabled(True)
            self.setCentralWidget(self.last_plugin)
            self.last_plugin.ismaximized = True
            # Workaround to solve an issue with editor's outline explorer:
            # (otherwise the whole plugin is hidden and so is the outline explorer
            #  and the latter won't be refreshed if not visible)
            self.last_plugin.show()
            self.last_plugin.visibility_changed(True)
            if self.last_plugin is self.editor:
                # Automatically show the outline if the editor was maximized:
                self.addDockWidget(Qt.RightDockWidgetArea,
                                   self.outlineexplorer.dockwidget)
                self.outlineexplorer.dockwidget.show()
        else:
            # Restore original layout (before maximizing current dockwidget)
            self.last_plugin.dockwidget.setWidget(self.last_plugin)
            self.last_plugin.dockwidget.toggleViewAction().setEnabled(True)
            self.setCentralWidget(None)
            self.last_plugin.ismaximized = False
            self.restoreState(self.state_before_maximizing)
            self.state_before_maximizing = None
            self.last_plugin.get_focus_widget().setFocus()
        self.__update_maximize_action()
        
    def __update_fullscreen_action(self):
        if self.isFullScreen():
            icon = "window_nofullscreen.png"
        else:
            icon = "window_fullscreen.png"
        self.fullscreen_action.setIcon(get_icon(icon))
    
    def update_edit_menu(self):
        """Update edit menu"""
        if self.menuBar().hasFocus():
            return
        # Disabling all actions to begin with
        for child in self.edit_menu.actions():
            child.setEnabled(False)        
        
        widget, textedit_properties = get_focus_widget_properties()
        if textedit_properties is None: # widget is not an editor/console
            return
        #!!! Below this line, widget is expected to be a QPlainTextEdit instance
        console, not_readonly, readwrite_editor = textedit_properties
        
        # Editor has focus and there is no file opened in it
        if not console and not_readonly and not self.editor.is_file_opened():
            return
        
        self.selectall_action.setEnabled(True)
        
        # Undo, redo
        self.undo_action.setEnabled( readwrite_editor \
                                     and widget.document().isUndoAvailable() )
        self.redo_action.setEnabled( readwrite_editor \
                                     and widget.document().isRedoAvailable() )

        # Copy, cut, paste, delete
        has_selection = widget.has_selected_text()
        self.copy_action.setEnabled(has_selection)
        self.cut_action.setEnabled(has_selection and not_readonly)
        self.paste_action.setEnabled(not_readonly)
        self.delete_action.setEnabled(has_selection and not_readonly)
        
        # Comment, uncomment, indent, unindent...
        if not console and not_readonly:
            # This is the editor and current file is writable
            for action in self.editor.edit_menu_actions:
                action.setEnabled(True)
        
    def update_search_menu(self):
        """Update search menu"""
        if self.menuBar().hasFocus():
            return        
        # Disabling all actions to begin with
        for child in [self.find_action, self.find_next_action,
                      self.find_previous_action, self.replace_action]:
            child.setEnabled(False)
        
        widget, textedit_properties = get_focus_widget_properties()
        for action in self.editor.search_menu_actions:
            action.setEnabled(self.editor.isAncestorOf(widget))
        if textedit_properties is None: # widget is not an editor/console
            return
        #!!! Below this line, widget is expected to be a QPlainTextEdit instance
        _x, _y, readwrite_editor = textedit_properties
        for action in [self.find_action, self.find_next_action,
                       self.find_previous_action]:
            action.setEnabled(True)
        self.replace_action.setEnabled(readwrite_editor)
        self.replace_action.setEnabled(readwrite_editor)

    def edit_preferences(self):
        """Edit Spyder preferences"""
        dlg = ConfigDialog(self)
        self.connect(dlg, SIGNAL("size_change(QSize)"),
                     lambda s: self.set_prefs_size(s))
        if self.prefs_dialog_size is not None:
            dlg.resize(self.prefs_dialog_size)
        for PrefPageClass in self.general_prefs:
            widget = PrefPageClass(dlg, main=self)
            widget.initialize()
            dlg.add_page(widget)
        for plugin in [self.workingdirectory, self.editor,
                       self.projectexplorer, self.extconsole, self.ipyconsole,
                       self.historylog, self.inspector, self.variableexplorer,
                       self.onlinehelp, self.explorer, self.findinfiles
                       ]:
#                        disable the thirdpart plugins
#                       ]+self.thirdparty_plugins:
            if plugin is not None:
                widget = plugin.create_configwidget(dlg)
                if widget is not None:
                    dlg.add_page(widget)
        if self.prefs_index is not None:
            dlg.set_current_index(self.prefs_index)
        dlg.show()
        dlg.check_all_settings()
        self.connect(dlg.pages_widget, SIGNAL("currentChanged(int)"),
                     self.__preference_page_changed)
        dlg.exec_()
        
    def __preference_page_changed(self, index):
        """Preference page index has changed"""
        self.prefs_index = index
        
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_flag = False
            self.showNormal()
            if self.maximized_flag:
                self.showMaximized()
        else:
            self.maximized_flag = self.isMaximized()
            self.fullscreen_flag = True
            self.showFullScreen()
        self.__update_fullscreen_action()
    
    def register_shortcut(self, qaction_or_qshortcut, context, name,
                          default=NoDefault):
        """
        Register QAction or QShortcut to Spyder main application,
        with shortcut (context, name, default)
        """
        self.shortcut_data.append((qaction_or_qshortcut,
                                    context, name, default))
        self.apply_shortcuts()
    
    def remove_deprecated_shortcuts(self):
        """Remove deprecated shortcuts"""
        data = [(context, name) for (qobject, context, name,
                default) in self.shortcut_data]
        remove_deprecated_shortcuts(data)
        
    def apply_shortcuts(self):
        """Apply shortcuts settings to all widgets/plugins"""
        toberemoved = []
        for index, (qobject, context, name,
                    default) in enumerate(self.shortcut_data):
            keyseq = QKeySequence(get_shortcut(context, name, default))
            try:
                if isinstance(qobject, QAction):
                    qobject.setShortcut(keyseq)
                elif isinstance(qobject, QShortcut):
                    qobject.setKey(keyseq)
            except RuntimeError:
                # Object has been deleted
                toberemoved.append(index)
        for index in sorted(toberemoved, reverse=True):
            self.shortcut_data.pop(index)
    
    def __update_maximize_action(self):
        if self.state_before_maximizing is None:
            text = "Maximize current plugin"
            tip = "Maximize current plugin"
            icon = "maximize.png"
        else:
            text = "Restore current plugin"
            tip = "Restore plugin to its original size"
            icon = "unmaximize.png"
        self.maximize_action.setText(text)
        self.maximize_action.setIcon(get_icon(icon))
        self.maximize_action.setToolTip(tip)
         
    def get_window_settings(self):
        """Return current window settings
        Symetric to the 'set_window_settings' setter"""
        size = self.window_size
        width, height = size.width(), size.height()
        is_fullscreen = self.isFullScreen()
        if is_fullscreen:
            is_maximized = self.maximized_flag
        else:
            is_maximized = self.isMaximized()
        pos = self.window_position
        posx, posy = pos.x(), pos.y()
        hexstate = qbytearray_to_str(self.saveState())
        return hexstate, width, height, posx, posy, is_maximized, is_fullscreen
    
    def setup_layout(self, default=False):
        """Setup window layout"""
        # prefix = ('lightwindow' if self.light else 'window') + '/'
        prefix = 'window/'
        (hexstate, window_size, prefs_dialog_size, pos, is_maximized,
         is_fullscreen) = self.load_window_settings(prefix, default)

        # if hexstate is None and not self.light:
        if hexstate is None:
            # First Spyder execution:
            # trying to set-up the dockwidget/toolbar positions to the best 
            # appearance possible
            splitting = (
                         (self.projectexplorer, self.editor, Qt.Horizontal),
                         (self.editor, self.outlineexplorer, Qt.Horizontal),
                         (self.outlineexplorer, self.inspector, Qt.Horizontal),
                         (self.inspector, self.console, Qt.Vertical),
                         )
            for first, second, orientation in splitting:
                if first is not None and second is not None:
                    self.splitDockWidget(first.dockwidget, second.dockwidget,
                                         orientation)
            for first, second in ((self.console, self.extconsole),
                                  (self.extconsole, self.ipyconsole),
                                  (self.ipyconsole, self.historylog),
                                  (self.inspector, self.variableexplorer),
                                  (self.variableexplorer, self.onlinehelp),
                                  (self.onlinehelp, self.explorer),
                                  (self.explorer, self.findinfiles),
                                  ):
                if first is not None and second is not None:
                    self.tabify_plugins(first, second)
                    
            
            for plugin in [self.findinfiles, self.onlinehelp, self.console,]:
                #+self.thirdparty_plugins:
                if plugin is not None:
                    plugin.dockwidget.close()
            
            for plugin in (self.inspector, self.extconsole):
                if plugin is not None:
                    plugin.dockwidget.raise_()
                    
            self.extconsole.setMinimumHeight(250)
            hidden_toolbars = [self.source_toolbar, self.edit_toolbar,
                               self.search_toolbar]
            for toolbar in hidden_toolbars:
                if toolbar is not None:
                    toolbar.close()
            for plugin in (self.projectexplorer, self.outlineexplorer):
                if plugin is not None:
                    plugin.dockwidget.close()
            
        self.set_window_settings(hexstate, window_size, prefs_dialog_size, pos,
                                 is_maximized, is_fullscreen)

        for plugin in self.widgetlist:
            plugin.initialize_plugin_in_mainwindow_layout()
    
    def reset_window_layout(self):
        """Reset window layout to default"""
        answer = QMessageBox.warning(self, _("Warning"),
                     _("Window layout will be reset to default settings: "
                       "this affects window position, size and dockwidgets.\n"
                       "Do you want to continue?"),
                     QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.setup_layout(default=True)
            
    def set_window_settings(self, hexstate, window_size, prefs_dialog_size,
                            pos, is_maximized, is_fullscreen):
        """Set window settings
        Symetric to the 'get_window_settings' accessor"""
        self.setUpdatesEnabled(False)
        self.window_size = QSize(window_size[0], window_size[1])  # width,height
        self.prefs_dialog_size = QSize(prefs_dialog_size[0],
                                       prefs_dialog_size[1])  # width,height
        self.window_position = QPoint(pos[0], pos[1])  # x,y
        self.setWindowState(Qt.WindowNoState)
        self.resize(self.window_size)
        self.move(self.window_position)
        # if not self.light:
        if True:
            # Window layout
            if hexstate:
                self.restoreState(QByteArray().fromHex(str(hexstate)))
                # [Workaround for Issue 880]
                # QDockWidget objects are not painted if restored as floating 
                # windows, so we must dock them before showing the mainwindow.
                for widget in self.children():
                    if isinstance(widget, QDockWidget) and widget.isFloating():
                        self.floating_dockwidgets.append(widget)
                        widget.setFloating(False)
            # Is fullscreen?
            if is_fullscreen:
                self.setWindowState(Qt.WindowFullScreen)
            self.__update_fullscreen_action()
        # Is maximized?
        if is_fullscreen:
            self.maximized_flag = is_maximized
        elif is_maximized:
            self.setWindowState(Qt.WindowMaximized)
        self.setUpdatesEnabled(True)
          
    def load_window_settings(self, prefix, default=False, section='main'):
        """Load window layout settings from userconfig-based configuration
        with *prefix*, under *section*
        default: if True, do not restore inner layout"""
        get_func = CONF.get_default if default else CONF.get
        window_size = get_func(section, prefix + 'size')
        prefs_dialog_size = get_func(section, prefix + 'prefs_dialog_size')
        if default:
            hexstate = None
        else:
            hexstate = get_func(section, prefix + 'state', None)
        pos = get_func(section, prefix + 'position')
        is_maximized = get_func(section, prefix + 'is_maximized')
        is_fullscreen = get_func(section, prefix + 'is_fullscreen')
        return hexstate, window_size, prefs_dialog_size, pos, is_maximized, \
               is_fullscreen
               
    def save_current_window_settings(self, prefix, section='main'):
        """Save current window settings with *prefix* in
        the userconfig-based configuration, under *section*"""
        win_size = self.window_size
        prefs_size = self.prefs_dialog_size
        
        CONF.set(section, prefix + 'size', (win_size.width(), win_size.height()))
#        CONF.set(section, prefix+'prefs_dialog_size',(prefs_size.width(), prefs_size.height()))
        CONF.set(section, prefix + 'is_maximized', self.isMaximized())
        CONF.set(section, prefix + 'is_fullscreen', self.isFullScreen())
        pos = self.window_position
        CONF.set(section, prefix + 'position', (pos.x(), pos.y()))
        if not self.light:
            self.maximize_dockwidget(restore=True)# Restore non-maximized layout
            qba = self.saveState()
            CONF.set(section, prefix+'state', qbytearray_to_str(qba))
            CONF.set(section, prefix+'statusbar',not self.statusBar().isHidden())

    #---- Global callbacks (called from plugins)
    def get_current_editor_plugin(self):
        """Return editor plugin which has focus:
        console, extconsole, editor, inspector or historylog"""
        if self.light:
            return self.extconsole
        widget = QApplication.focusWidget()
        from SMlib.widgets.editor import TextEditBaseWidget
        from SMlib.widgets.shell import ShellBaseWidget
        if not isinstance(widget, (TextEditBaseWidget, ShellBaseWidget)):
            return
        for plugin in self.widgetlist:
            if plugin.isAncestorOf(widget):
                return plugin
        else:
            # External Editor window
            plugin = widget
            from SMlib.widgets.editor import EditorWidget
            while not isinstance(plugin, EditorWidget):
                plugin = plugin.parent()
            return plugin         
    
    def set_prefs_size(self, size):
        """Save preferences dialog size"""
        self.prefs_dialog_size = size
    
    def find(self):
        """Global find callback"""
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.show()
            plugin.find_widget.search_text.setFocus()
            return plugin
    
    def find_next(self):
        """Global find next callback"""
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.find_next()
            
    def find_previous(self):
        """Global find previous callback"""
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.find_previous()
        
    def replace(self):
        """Global replace callback"""
        plugin = self.find()
        if plugin is not None:
            plugin.find_widget.show_replace()

    def global_callback(self):
        """Global callback"""
        widget = QApplication.focusWidget()
        action = self.sender()
        callback = from_qvariant(action.data(), unicode)
        from SMlib.widgets.editor import TextEditBaseWidget
        if isinstance(widget, TextEditBaseWidget):
            getattr(widget, callback)()
        
    def redirect_internalshell_stdio(self, state):
        if state:
            self.console.shell.interpreter.redirect_stds()
        else:
            self.console.shell.interpreter.restore_stds()
        
    def open_external_console(self, fname, wdir, args, interact, debug, python,
                              python_args, systerm):
        """Open external console"""
        if systerm:
            # Running script in an external system terminal
            try:
                programs.run_python_script_in_terminal(fname, wdir, args,
                                                interact, debug, python_args)
            except NotImplementedError:
                QMessageBox.critical(self, _("Run"),
                                     _("Running an external system terminal "
                                       "is not supported on platform %s."
                                       ) % os.name)
        else:
            self.extconsole.visibility_changed(True)
            self.extconsole.raise_()
            self.extconsole.start(
                fname=unicode(fname), wdir=unicode(wdir), args=unicode(args),
                interact=interact, debug=debug, python=python,
                python_args=unicode(python_args) )
        
    def execute_in_external_console(self, lines, focus_to_editor):
        """Execute lines in external or IPython console 
        and eventually set focus to editor"""
        console = self.extconsole
        if self.ipyconsole is None\
           or self.last_console_plugin_focus_was_python:
            console = self.extconsole
        else:
            console = self.ipyconsole
        console.visibility_changed(True)
        console.raise_()
        console.execute_python_code(lines)
        if focus_to_editor:
           self.editor.visibility_changed(True)
        
    def open_file(self, fname, external=False):
        """
        Open filename with the appropriate application
        Redirect to the right widget (txt -> editor, spydata -> workspace, ...)
        or open file outside Spyder (if extension is not supported)
        """
        fname = unicode(fname)
        ext = osp.splitext(fname)[1]
        if ext in EDIT_EXT:
            self.editor.load(fname)
        elif self.variableexplorer is not None and ext in IMPORT_EXT\
             and ext in ('.spydata', '.mat', '.npy', '.h5'):
            self.variableexplorer.import_data(fname)
        elif not external:
            fname = file_uri(fname)
            programs.start_file(fname)
    
    def open_external_file(self, fname):
        """
        Open external files that can be handled either by the Editor or the
        variable explorer inside Spyder.
        """
        if osp.isfile(fname):
            self.open_file(fname, external=True)
        elif osp.isfile(osp.join(CWD, fname)):
            self.open_file(osp.join(CWD, fname), external=True)
            

    def resizeEvent(self, event):
        """Reimplement Qt method"""
        if not self.isMaximized() and not self.fullscreen_flag:
            self.window_size = self.size()
        QMainWindow.resizeEvent(self, event)
    
    def moveEvent(self, event):
        """Reimplement Qt method"""
        if not self.isMaximized() and not self.fullscreen_flag:
            self.window_position = self.pos()
        QMainWindow.moveEvent(self, event)
    
    def tabify_plugins(self, first, second):
        """Tabify plugin dockwigdets"""
        self.tabifyDockWidget(first.dockwidget, second.dockwidget)
        
    def remove_tmpdir(self):
        """Remove Spyder temporary directory"""
        shutil.rmtree(programs.TEMPDIR, ignore_errors=True)
        
    def apply_settings(self):
        """Apply settings changed in 'Preferences' dialog box"""
        qapp = QApplication.instance()
        qapp.setStyle(CONF.get('main', 'windows_style', self.default_style))
        
        default = self.DOCKOPTIONS
        if CONF.get('main', 'vertical_tabs'):
            default = default|QMainWindow.VerticalTabs
        if CONF.get('main', 'animated_docks'):
            default = default|QMainWindow.AnimatedDocks
        self.setDockOptions(default)
        
        for child in self.widgetlist:
            features = child.FEATURES
            if CONF.get('main', 'vertical_dockwidget_titlebars'):
                features = features|QDockWidget.DockWidgetVerticalTitleBar
            child.dockwidget.setFeatures(features)
            child.update_margins()
        
        self.apply_statusbar_settings()
        
    def apply_statusbar_settings(self):
        """Update status bar widgets settings"""
        for widget, name in ((self.mem_status, 'memory_usage'),
                             (self.cpu_status, 'cpu_usage')):
            if widget is not None:
                widget.setVisible(CONF.get('main', '%s/enable' % name))
                widget.set_interval(CONF.get('main', '%s/timeout' % name))
        
    def post_visible_setup(self):
        """Actions to be performed only after the main window's `show` method 
        was triggered"""
        self.emit(SIGNAL('restore_scrollbar_position()'))
        if self.projectexplorer is not None:
            self.projectexplorer.check_for_io_errors()
        
        # Remove our temporary dir
        atexit.register(self.remove_tmpdir)
        
        # Remove settings test directory
        if TEST is not None:
            import tempfile
            conf_dir = osp.join(tempfile.gettempdir(), SUBFOLDER)
            atexit.register(shutil.rmtree, conf_dir, ignore_errors=True)

        # [Workaround for Issue 880]
        # QDockWidget objects are not painted if restored as floating 
        # windows, so we must dock them before showing the mainwindow,
        # then set them again as floating windows here.
        for widget in self.floating_dockwidgets:
            widget.setFloating(True)

        # In MacOS X 10.7 our app is not displayed after initialized (I don't
        # know why because this doesn't happen when started from the terminal),
        # so we need to resort to this hack to make it appear.
        if sys.platform == 'darwin' and 'Spyder.app' in __file__:
            import subprocess
            idx = __file__.index('Spyder.app')
            app_path = __file__[:idx]
            subprocess.call(['open', app_path + 'Spyder.app'])

        # Server to maintain just one Spyder instance and open files in it if
        # the user tries to start other instances with
        # $ spyder foo.py
        if CONF.get('main', 'single_instance') and not self.new_instance:
            t = threading.Thread(target=self.start_open_files_server)
            t.setDaemon(True)
            t.start()
        
            # Connect the window to the signal emmited by the previous server
            # when it gets a client connected to it
            self.connect(self, SIGNAL('open_external_file(QString)'),
                         lambda fname: self.open_external_file(fname))
        
        # Open a Python or IPython console at startup
        # NOTE: Leave this at the end of post_visible_setup because
        #       it seems to avoid being unable to start a console at
        #       startup *sometimes* if using PySide
        if self.light:
            self.extconsole.open_interpreter()
        else:
            self.extconsole.open_interpreter_at_startup()
        self.extconsole.setMinimumHeight(0)
    
    def pythonpath_changed(self):
        """Project Explorer PYTHONPATH contribution has changed"""
        self.remove_path_from_sys_path()
        self.project_path = self.projectexplorer.get_pythonpath()
        self.add_path_to_sys_path()
        self.emit(SIGNAL("pythonpath_changed()"))

#---- PYTHONPATH management, etc.
    def get_spyder_pythonpath(self):
        """Return Spyder PYTHONPATH"""
        return self.path+self.project_path
    def add_path_to_sys_path(self):
        """Add Spyder path to sys.path"""
        for path in reversed(self.get_spyder_pythonpath()):
            sys.path.insert(1, path)

    def remove_path_from_sys_path(self):
        """Remove Spyder path from sys.path"""
        sys_path = sys.path
        while sys_path[1] in self.get_spyder_pythonpath():
            sys_path.pop(1)

    def path_manager_callback(self):
        """Spyder path manager"""
        self.remove_path_from_sys_path()
        project_pathlist = self.projectexplorer.get_pythonpath()
        dialog = PathManager(self, self.path, project_pathlist, sync=True)
        self.connect(dialog, SIGNAL('redirect_stdio(bool)'),
                     self.redirect_internalshell_stdio)
        dialog.exec_()
        self.add_path_to_sys_path()
        encoding.writelines(self.path, self.SM_path) # Saving path
        self.emit(SIGNAL("pythonpath_changed()"))
        
    def start_open_files_server(self):
        self.open_files_server.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_REUSEADDR, 1)
        port = select_port(default_port=OPEN_FILES_PORT)
        CONF.set('main', 'open_files_port', port)
        self.open_files_server.bind(('127.0.0.1', port))
        self.open_files_server.listen(20)
        while 1:  # 1 is faster than True
            try:
                req, dummy = self.open_files_server.accept()
            except socket.error as e:
                # See Issue 1275 for details on why errno EINTR is
                # silently ignored here.
                eintr = errno.WSAEINTR if os.name == 'nt' else errno.EINTR
                if e.args[0] == eintr:
                    continue
                raise
            fname = req.recv(1024)
            if not self.light:
                self.emit(SIGNAL('open_external_file(QString)'), fname)
            req.sendall(' ')

            
#==============================================================================
# Spyder's main window widgets utilities
#==============================================================================
def get_focus_python_shell():
    """Extract and return Python shell from widget
    Return None if *widget* is not a Python shell (e.g. IPython kernel)"""
    widget = QApplication.focusWidget()
    from SMlib.widgets.shell import PythonShellWidget
    from SMlib.widgets.externalshell.pythonshell import ExternalPythonShell
    if isinstance(widget, PythonShellWidget):
        return widget
    elif isinstance(widget, ExternalPythonShell):
        return widget.shell

def get_focus_widget_properties():
    """Get properties of focus widget
    Returns tuple (widget, properties) where properties is a tuple of
    booleans: (is_console, not_readonly, readwrite_editor)"""
    widget = QApplication.focusWidget()
    from SMlib.widgets.shell import ShellBaseWidget
    from SMlib.widgets.editor import TextEditBaseWidget
    textedit_properties = None
    if isinstance(widget, (ShellBaseWidget, TextEditBaseWidget)):
        console = isinstance(widget, ShellBaseWidget)
        not_readonly = not widget.isReadOnly()
        readwrite_editor = not_readonly and not console
        textedit_properties = (console, not_readonly, readwrite_editor)
    return widget, textedit_properties

 
        
def run():
    ''
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName('Gui_SM')
    app.setApplicationVersion('1.0')
    main = MainWindow()
    main.setUp()
    main.show()
    main.post_visible_setup()
    app.exec_()
    
    
if __name__ == '__main__':
     run()    
