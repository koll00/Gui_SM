from PyQt4 import QtGui, QtCore

class console(QtGui.QPlainTextEdit):
    def __init__(self, parent=None):
       super(console, self).__init__(parent) 
       
class monitor(QtGui.QWidget):
    def __init__(self, parent=None):
        super(monitor, self).__init__(parent)