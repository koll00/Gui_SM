'''
    
'''
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QVariant
#from actions import *
'''
    Create the MainWindow for the application, it contains ui and action
'''

import qrc_app


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createWorkWindow()
        
        self.readSettings()
        
        self.setWindowTitle("Gui_SM")
        
        self.newLetter()
        self.setUnifiedTitleAndToolBarOnMac(True)
     
    def closeEvent(self, event):
        self.writeSettings()
#            event.ignore()
    def newFile(self):
        ''
    def createActions(self):
        self.newAct = QtGui.QAction(QtGui.QIcon(':/icons/new.png'), "&New",
                self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/icons/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/icons/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)
        
        self.cutAct = QtGui.QAction(QtGui.QIcon(':/icons/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.textEdit.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/icons/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.textEdit.copy)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/icons/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.textEdit.paste)
        
        'initial the cut copy status'
        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.textEdit.copyAvailable.connect(self.cutAct.setEnabled)
        self.textEdit.copyAvailable.connect(self.copyAct.setEnabled)
        
    def createMenus(self):
        'initial the menus for system'
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator();
#         self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        
        self.viewMenu = self.menuBar().addMenu("&View")

        self.helpMenu = self.menuBar().addMenu("&Help")
#         self.helpMenu.addAction(self.aboutAct)
#         self.helpMenu.addAction(self.aboutQtAct)
            
    def createToolBars(self):
        'initial the tool bar'
        self.fileToolBar = self.addToolBar("File")
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        
        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)
         
    def createStatusBar(self):
       ''
       self.statusBar().showMessage("Ready")
       
    def createWorkWindow(self):
        ''
        
    def readSettings(self):
        'initial the application gui by the config from QSetting'
        settings = QtCore.QSettings("sm", "Application")
        
        pos = settings.value("pos", QVariant(QtCore.QPoint(0, 0))).toPoint()
        size = settings.value("size", QVariant(QtCore.QSize(1024, 600))).toSize()
        
        self.resize(size)
        self.move(pos)   

    def writeSettings(self):
        'record the pos and size of the application when closed'
        settings = QtCore.QSettings("sm", "Application")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        
    def newFile(self):
        ''
    def open(self):
        ''
    def save(self):
        ''