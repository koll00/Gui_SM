import sys, os
sys.path.append('..' + os.path.sep)
import os.path as osp
import atexit
import shutil

from SMlib.plugins.ipythonConsole import IPythonConsole
from SMlib.plugins.externalconsole import ExternalConsole

from PyQt4.QtGui import QMainWindow, QApplication, QAction,QDockWidget, QShortcut, QMenu, QMessageBox

from PyQt4.Qt import QKeySequence
from PyQt4.QtCore import SIGNAL, Qt, QSize, QPoint,QByteArray


from SMlib.configs.baseconfig import debug_print, _, TEST, get_conf_path
from SMlib.configs.userconfig import NoDefault 
from SMlib.configs.guiconfig import get_shortcut, remove_deprecated_shortcuts
from SMlib.config import CONF
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


class MainWindow(QMainWindow):
    SM_path = get_conf_path('.path')
    
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        
        self.light = False
        self.new_instance = True
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
        ''
        # List of satellite widgets (registered in add_dockwidget):
        self.widgetlist = []
        
        # Flags used if closing() is called by the exit() shell command
        self.already_closed = False
        self.is_starting_up = True
        
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
       
    def debug_print(self, message):
        """Debug prints"""
        debug_print(message)
         
    def setUp(self):
        """Setup main window"""
        
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        #self.initalStatus()
        self.extconsole = ExternalConsole(self, light_mode=self.light)
        self.extconsole.register_plugin()
        
        
        self.ipyconsole = IPythonConsole(self)
        self.ipyconsole.register_plugin()
        
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
        '''    
#         self.undo_action = QtGui.QAction(QtGui.QIcon(':/icons/undo.png'),
#                                          "&Undo", self, shortcut="Ctrl+Z",
#                                          statusTip="undo the operation",
#                                          triggered=self.undo)

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
        self.redo_action = QtGui.QAction(QtGui.QIcon(':/icons/redo.png'),
                                         "&Redo", self, shortcut="Ctrl+Y",
                                         statusTip="redo the operation",
                                         triggered=self.redo)
        
        self.edit_menu_actions = [self.undo_action, self.redo_action,
                                      None, self.cut_action, self.copy_action,
                                      self.paste_action]
        
        quit_action = QtGui.QAction(QtGui.QIcon(':/icons/redo.png'),
                                         "&Quit", self, shortcut="Ctrl+Q",
                                         statusTip="Quit",
                                         triggered=self.redo)
        self.file_menu_actions += [quit_action]
#         self.newConsoleAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Console",
#                 self, statusTip="Create a new console", triggered=self.newConsole)
#         
#         self.newMonitorAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Monitor",
#                 self, statusTip="Create a new console", triggered=self.newMonitor)
'''
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
        
        
    def createMenus(self):
        'initial the menus for system'
        # File menu
        self.file_menu = self.menuBar().addMenu(_("&File"))
        # Edit menu
        self.edit_menu = self.menuBar().addMenu(_("&Edit"))
        # search_menu
        self.search_menu = self.menuBar().addMenu(_("&Search"))
        # View menu
        self.view_menu = self.menuBar().addMenu(_("&View"))
        # Help menu
        self.help_menu = self.menuBar().addMenu(_("&Help"))
        
        add_actions(self.file_menu, self.file_menu_actions)
        add_actions(self.edit_menu, self.edit_menu_actions)
        add_actions(self.search_menu, self.search_menu_actions)
        
        self.view_menu.addMenu(self.windows_toolbars_menu)
        
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
        
        add_actions(self.main_toolbar, self.main_toolbar_actions)
        add_actions(self.file_toolbar, self.file_toolbar_actions)
        add_actions(self.edit_toolbar, self.edit_toolbar_actions)
        add_actions(self.search_toolbar, self.search_toolbar_actions)
        
    def createStatusBar(self):
        ''
        status = self.statusBar()
        status.setObjectName("StatusBar")
        status.showMessage("Ready", 5000)
    
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
            from spyderlib.widgets.externalshell import pythonshell
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
                        
    def global_callback(self):
        """Global callback"""
        widget = QApplication.focusWidget()
        action = self.sender()
        callback = from_qvariant(action.data(), unicode)
        from SMlib.widgets.sourcecode.base import TextEditBaseWidget
        if isinstance(widget, TextEditBaseWidget):
            getattr(widget, callback)()
            
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
                    
            '''
            for plugin in [self.findinfiles, self.onlinehelp, self.console,]+self.thirdparty_plugins:
                if plugin is not None:
                    plugin.dockwidget.close()
            for plugin in (self.inspector, self.extconsole):
                if plugin is not None:
                    plugin.dockwidget.raise_()
                    '''
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
    '''
    def get_current_editor_plugin(self):
        """Return editor plugin which has focus:
        console, extconsole, editor, inspector or historylog"""
        if self.light:
            return self.extconsole
        widget = QApplication.focusWidget()
        from spyderlib.widgets.editor import TextEditBaseWidget
        from spyderlib.widgets.shell import ShellBaseWidget
        if not isinstance(widget, (TextEditBaseWidget, ShellBaseWidget)):
            return
        for plugin in self.widgetlist:
            if plugin.isAncestorOf(widget):
                return plugin
        else:
            # External Editor window
            plugin = widget
            from spyderlib.widgets.editor import EditorWidget
            while not isinstance(plugin, EditorWidget):
                plugin = plugin.parent()
            return plugin         
    '''
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
        print self.tabifyDockWidget(first.dockwidget, second.dockwidget)
        
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
#==============================================================================
# Spyder's main window widgets utilities
#==============================================================================
def get_focus_python_shell():
    """Extract and return Python shell from widget
    Return None if *widget* is not a Python shell (e.g. IPython kernel)"""
    widget = QApplication.focusWidget()
    from spyderlib.widgets.shell import PythonShellWidget
    from spyderlib.widgets.externalshell.pythonshell import ExternalPythonShell
    if isinstance(widget, PythonShellWidget):
        return widget
    elif isinstance(widget, ExternalPythonShell):
        return widget.shell

def get_focus_widget_properties():
    """Get properties of focus widget
    Returns tuple (widget, properties) where properties is a tuple of
    booleans: (is_console, not_readonly, readwrite_editor)"""
    widget = QApplication.focusWidget()
    from spyderlib.widgets.shell import ShellBaseWidget
    from spyderlib.widgets.editor import TextEditBaseWidget
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
   # main.post_visible_setup()
    app.exec_()
    
    
if __name__ == '__main__':
     run()    