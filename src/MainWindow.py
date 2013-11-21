'''
    Create the MainWindow for the application, it contains ui and action
'''
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QVariant
#from actions import *
import qrc_app
from  workSpace import *

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.isUntitled = True
        
        self.mdiArea = QtGui.QMdiArea()
        
        self.setCentralWidget(self.mdiArea)
        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiLayout = QtGui.QGridLayout()
        self.mdiLayout.setMargin(0)
        self.mdiArea.setLayout(self.mdiLayout)
        
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createWorkWindow()
        self.initalStatus()
        
        self.readSettings()
        
        self.setWindowTitle("Gui_SM")
        
        self.setUnifiedTitleAndToolBarOnMac(True)

     
    def closeEvent(self, event):
        self.writeSettings()
#            event.ignore()
    def documentWasModified(self):
        self.setWindowModified(True)
        
    def newFile(self):
        ''
    def createActions(self):
#         self.newAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&New",
#                 self, shortcut=QtGui.QKeySequence.New,
#                 statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/icons/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/icons/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)
        
        self.cutAct = QtGui.QAction(QtGui.QIcon(':/icons/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/icons/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.copy)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/icons/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.paste)
        
        self.newConsoleAct =  QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Console",
                self, statusTip="Create a new console", triggered=self.newConsole)
        
        self.newMonitorAct =  QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&Monitor",
                self, statusTip="Create a new console", triggered=self.newMonitor)
       
    def createMenus(self):
        'initial the menus for system'
        self.fileMenu = self.menuBar().addMenu("&File")
        self.new = self.fileMenu.addMenu("&New")
        self.new.addAction(self.newConsoleAct)
        self.new.addAction(self.newMonitorAct)
        
#         self.fileMenu.addAction(self.newAct)
        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        
        
#        self.fileMenu.addAction(self.saveAsAct)
        
#         self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.newConsoleAct)
        
        
        self.helpMenu = self.menuBar().addMenu("&Help")
#         self.helpMenu.addAction(self.aboutAct)
#         self.helpMenu.addAction(self.aboutQtAct)
            
    def createToolBars(self):
        'initial the tool bar'
        self.fileToolBar = self.addToolBar("File")
#        self.fileToolBar.addAction(self.new)
        self.fileToolBar.addAction(self.openAct)
        
        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)
        
        self.workSpace = QtGui.QToolBar('workSpace')
        self.workSpace.addAction(self.newConsoleAct)
        self.workSpace.addAction(self.newMonitorAct)
        self.addToolBar(1, self.workSpace )
        
    def createStatusBar(self):
       ''
       self.statusBar().showMessage("Ready")
       
    def createWorkWindow(self):
        ''
        
        
    def initalStatus(self):
        'initial the cut copy status'
        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
    def readSettings(self):
        'initial the application gui by the config from QSetting'
        settings = QtCore.QSettings("sm", "Application")
        '''
        ps: I will fix later
        self.restoreGeometry(settings.value('mainWindow/geometry').toByteArray())
        self.restoreState(settings.value('mainWindow/status').toByteArray())
        '''
        pos = settings.value("pos", QVariant(QtCore.QPoint(0, 0))).toPoint()
        size = settings.value("size", QVariant(QtCore.QSize(1024, 600))).toSize()
        
        self.resize(size)
        self.move(pos)

    def writeSettings(self):
        'record the pos and size of the application when closed'
        settings = QtCore.QSettings("sm", "Application")
        '''
        ps: I will fix later
        settings.setValue('geometry',self.saveGeometry())
        settings.setValue('status', self.saveState())
        '''
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
    
    
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
    def newConsole(self):
        ''
        self.con = console(self)
        self.con.copyAvailable.connect(self.cutAct.setEnabled)
        self.con.copyAvailable.connect(self.copyAct.setEnabled)
        self.mdiLayout.addWidget(self.con,0,0)

    def newMonitor(self):
        self.mdiLayout.addWidget(QtGui.QDockWidget(self),0,1)
#        self.mdiLayout.addWidget(monitor())
        
    def activeMdiChild(self):
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None