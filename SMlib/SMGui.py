
from PyQt4.QtGui import QMainWindow, QApplication
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL 

import qrc_app

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        
        
        self.extconsole = None
        self.ipyconsole = None
        
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
        
    def setUp(self):
        """Setup main window"""
        
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        #self.initalStatus()
        
    def createActions(self):
#         self.newAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&New",
#                 self, shortcut=QtGui.QKeySequence.New,
#                 statusTip="Create a new file", triggered=self.newFile)
        #self.debug_print("  ..core action")
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
        
#         self.newConsoleAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Console",
#                 self, statusTip="Create a new console", triggered=self.newConsole)
#         
#         self.newMonitorAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Monitor",
#                 self, statusTip="Create a new console", triggered=self.newMonitor)
       
    def createMenus(self):
        'initial the menus for system'
        #File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.new = self.file_menu.addMenu("&New")
        #self.new.addAction(self.newConsoleAct)
        #self.new.addAction(self.newMonitorAct)
        
#         self.file_menu.addAction(self.newAct)
        self.file_menu.addSeparator();
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        
        
#        self.file_menu.addAction(self.saveAsAct)
        
#         self.file_menu.addAction(self.exitAct)
        #Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.cut_action)
        self.edit_menu.addAction(self.copy_action)
        self.edit_menu.addAction(self.paste_action)
        
        self.view_menu = self.menuBar().addMenu("&View")
        # View menu
        self.windows_toolbars_menu = QtGui.QMenu("Windows and toolbars", self)
        self.connect(self.windows_toolbars_menu, SIGNAL("aboutToShow()"),self.update_windows_toolbars_menu)
        self.view_menu.addMenu(self.windows_toolbars_menu)
        
        #Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
#         self.helpMenu.addAction(self.aboutAct)
#         self.helpMenu.addAction(self.aboutQtAct)
            
    def createToolBars(self):
        'initial the tool bar'
        self.fileToolBar = self.addToolBar("File")
#        self.fileToolBar.addAction(self.new)
        self.fileToolBar.addAction(self.open_action)
        
        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.addAction(self.cut_action)
        self.editToolBar.addAction(self.copy_action)
        self.editToolBar.addAction(self.paste_action)
        
        self.workSpace = QtGui.QToolBar('workSpace')
        #self.workSpace.addAction(self.newConsoleAct)
        #self.workSpace.addAction(self.newMonitorAct)
        self.addToolBar(1, self.workSpace)
        
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
        ''
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
    