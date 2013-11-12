'''
    This script is created for transfer source to py
'''

import os
#os.system("pyuic4 ../ui/mainWindow.ui -o ../src/ui_source/ui_mainWindow.py")

'transfer the qrc resource to py'
os.system("pyrcc4 -o ../src/qrc_app.py ../src/app.qrc")