import sys, os 
sys.path.append('..' + os.path.sep)

from PyQt4.QtGui import QMainWindow, QApplication, QAction
from PyQt4 import QtGui, QtCore
from PyQt4.Qt import QKeySequence
from PyQt4.QtCore import SIGNAL, Qt, QSize, QPoint
import qrc_app

from SMlib.configs.baseconfig import debug_print, _
from SMlib.configs.userconfig import NoDefault 
from SMlib.configs.guiconfig import get_shortcut
from SMlib.config import CONF
from SMlib.py3compat import qbytearray_to_str
from SMlib.configs.baseconfig import debug_print
from SMlib.utils.qthelpers import (create_action, add_actions, get_icon,
                                       get_std_icon, add_shortcut_to_tooltip,
                                       create_module_bookmark_actions,
                                       create_bookmark_action,
                                       create_program_action, DialogManager,
                                       keybinding, qapplication,
                                       create_python_script_action, file_uri)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        
        
        # Shortcut management data
        self.shortcut_data = []
        
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
        # self.initalStatus()
        
        # Window set-up
        self.debug_print("Setting up window...")
        self.setup_layout(default=False)
        
    def createActions(self):
#         self.newAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&New",
#                 self, shortcut=QtGui.QKeySequence.New,
#                 statusTip="Create a new file", triggered=self.newFile)
        # self.debug_print("  ..core action")
        self.open_action = QtGui.QAction(QtGui.QIcon(':/icons/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.save_action = QtGui.QAction(QtGui.QIcon(':/icons/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)
        
        self.cut_action = QtGui.QAction(QtGui.QIcon(':/icons/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.cut)

        self.copy_action = QtGui.QAction(QtGui.QIcon(':/icons/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.copy)

        self.paste_action = QtGui.QAction(QtGui.QIcon(':/icons/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.paste)
        
        self.undo_action = QtGui.QAction(QtGui.QIcon(':/icons/undo.png'),
                                         "&Undo", self, shortcut="Ctrl+Z",
                                         statusTip="undo the operation",
                                         triggered=self.undo)
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
        self.maximize_action = create_action(self, 'maximize',
                                            triggered=self.maximize_dockwidget)
        self.register_shortcut(self.maximize_action, "_",
                                   "Maximize dockwidget", "Ctrl+Alt+Shift+M")
        self.__update_maximize_action()
            
        # Fullscreen mode
        self.fullscreen_action = create_action(self,
                                            "Fullscreen mode",
                                            triggered=self.toggle_fullscreen)
        self.register_shortcut(self.fullscreen_action, "_",
                                   "Fullscreen mode", "F11")
        add_shortcut_to_tooltip(self.fullscreen_action, context="_",
                                    name="Fullscreen mode")
            
        # Main toolbar
        self.main_toolbar_actions = [self.maximize_action,
                                         self.fullscreen_action
                                         ]
            
    def createMenus(self):
        'initial the menus for system'
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        
        add_actions(self.file_menu, self.file_menu_actions)
        add_actions(self.edit_menu, self.edit_menu_actions)
        
    
    #---- Window setup
    def create_toolbar(self, title, object_name, iconsize=24):
        """Create and return toolbar with *title* and *object_name*"""
        toolbar = self.addToolBar(title)
        toolbar.setObjectName(object_name)
        toolbar.setIconSize(QSize(iconsize, iconsize))
        return toolbar
    
    def createToolBars(self):
        'initial the tool bar'
        self.main_toolbar = self.create_toolbar("Main_toolbar", "main_toolbar")
        self.file_toolbar = self.create_toolbar("File", "file")
        self.edit_toolbar = self.create_toolbar("Edit", "edit")
        
        
        add_actions(self.main_toolbar, self.main_toolbar_actions)
        add_actions(self.file_toolbar, self.file_toolbar_actions)
        add_actions(self.edit_toolbar, self.edit_toolbar_actions)
        
    def createStatusBar(self):
        ''
        status = self.statusBar()
        status.setObjectName("StatusBar")
        status.showMessage("Ready", 5000)
        
    def update_windows_toolbars_menu(self):
        """Update windows&toolbars menu"""
        self.windows_toolbars_menu.clear()
        popmenu = self.createPopupMenu()
#        add_actions(self.windows_toolbars_menu, popmenu.actions())

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
#         self.dialog_manager.close_all()
        self.already_closed = True
#        if CONF.get('main', 'single_instance'):
#            self.open_files_server.close()
        return True
    
    def newFile(self):
        ''
    def open(self):
        ''
    def save(self):
        ''
    def cut(self):
        ''
    def copy(self):
        ''
    def paste(self):
        ''
    def undo(self):
        print "undo"
    def redo(self):
        print "redo"
        
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
            """
            for plugin in [self.findinfiles, self.onlinehelp, self.console,]+self.thirdparty_plugins:
                if plugin is not None:
                    plugin.dockwidget.close()
            for plugin in (self.inspector, self.extconsole):
                if plugin is not None:
                    plugin.dockwidget.raise_()
            self.extconsole.setMinimumHeight(250)
            hidden_toolbars = [self.source_toolbar, self.edit_toolbar,
                               self.search_toolbar]
            for toolbar in hidden_toolbars:
                toolbar.close()
            for plugin in (self.projectexplorer, self.outlineexplorer):
                plugin.dockwidget.close()
            """
        self.set_window_settings(hexstate, window_size, prefs_dialog_size, pos,
                                 is_maximized, is_fullscreen)

        for plugin in self.widgetlist:
            plugin.initialize_plugin_in_mainwindow_layout()
    
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
#         if not self.light:
#             self.maximize_dockwidget(restore=True)# Restore non-maximized layout
#             qba = self.saveState()
#             CONF.set(section, prefix+'state', qbytearray_to_str(qba))
#             CONF.set(section, prefix+'statusbar',not self.statusBar().isHidden())
    
    def add_dockwidget(self, child):
        """Add QDockWidget and toggleViewAction"""
        dockwidget, location = child.create_dockwidget()
        if CONF.get('main', 'vertical_dockwidget_titlebars'):
            dockwidget.setFeatures(dockwidget.features() | 
                                   QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(location, dockwidget)
        self.widgetlist.append(child)
        
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
        
    def __update_fullscreen_action(self):
        if self.isFullScreen():
            icon = "window_nofullscreen.png"
        else:
            icon = "window_fullscreen.png"
        # self.fullscreen_action.setIcon(get_icon(icon))
        
def run():
    ''
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName('Gui_SM')
    app.setApplicationVersion('1.0')
    main = MainWindow()
    main.setUp()
    main.show()
    app.exec_()
    
    
if __name__ == '__main__':
    run()
    
