'''
    The main program to run
'''

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
from MainWindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Gui_SM')
    app.setApplicationVersion('1.0')
    window = MainWindow();
    window.show()
    app.exec_()

if __name__ == '__main__':
    main();