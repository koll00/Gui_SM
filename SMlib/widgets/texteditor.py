# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see SMlib/__init__.py for details)

"""
Text Editor Dialog based on Qt
"""

from PyQt4.QtCore import Qt, SIGNAL, SLOT
from PyQt4.QtGui import QVBoxLayout, QTextEdit, QDialog, QDialogButtonBox

# Local import
from SMlib.configs.baseconfig import _
from SMlib.configs.guiconfig import get_font
from SMlib.utils.qthelpers import get_icon


class TextEditor(QDialog):
    """Array Editor Dialog"""
    def __init__(self, text, title='', font=None, parent=None,
                 readonly=False, size=(400, 300)):
        QDialog.__init__(self, parent)
        
        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.text = None
        
        self._conv = str if isinstance(text, str) else unicode
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Text edit
        self.edit = QTextEdit(parent)
        self.connect(self.edit, SIGNAL('textChanged()'), self.text_changed)
        self.edit.setReadOnly(readonly)
        self.edit.setPlainText(text)
        if font is None:
            font = get_font('texteditor')
        self.edit.setFont(font)
        self.layout.addWidget(self.edit)

        # Buttons configuration
        buttons = QDialogButtonBox.Ok
        if not readonly:
            buttons = buttons | QDialogButtonBox.Cancel
        bbox = QDialogButtonBox(buttons)
        self.connect(bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(bbox, SIGNAL("rejected()"), SLOT("reject()"))
        self.layout.addWidget(bbox)
        
        # Make the dialog act as a window
        self.setWindowFlags(Qt.Window)
        
        self.setWindowIcon(get_icon('edit.png'))
        self.setWindowTitle(_("Text editor") + \
                            "%s" % (" - "+str(title) if str(title) else ""))
        self.resize(size[0], size[1])
    
    def text_changed(self):
        """Text has changed"""
        self.text = self._conv(self.edit.toPlainText())
        
    def get_value(self):
        """Return modified text"""
        # It is import to avoid accessing Qt C++ object as it has probably
        # already been destroyed, due to the Qt.WA_DeleteOnClose attribute
        return self.text
    
    
def test():
    """Text editor demo"""
    from SMlib.utils.qthelpers import qapplication
    _app = qapplication()  # analysis:ignore
    dialog = TextEditor("""
    01234567890123456789012345678901234567890123456789012345678901234567890123456789
    dedekdh elkd ezd ekjd lekdj elkdfjelfjk e
    """)
    dialog.show()
    if dialog.exec_():
        text = dialog.get_value()
        print "Accepted:", text
        dialog = TextEditor(text)
        dialog.exec_()
    else:
        print "Canceled"

if __name__ == "__main__":
    test()