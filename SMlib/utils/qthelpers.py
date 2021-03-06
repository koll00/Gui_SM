"""Qt utilities"""
import sys,os 
sys.path.append('..'+ os.path.sep + '..' + os.path.sep)

from PyQt4.QtGui import (QAction, QStyle, QWidget, QIcon, QApplication,
                                QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
                                QKeyEvent, QMenu, QKeySequence, QToolButton,
                                QPixmap, QFileDialog)
from PyQt4.QtCore import (SIGNAL, QObject, Qt, QLocale, QTranslator,
                                 QLibraryInfo, QEvent)

import re
import os.path as osp

# Local import
from SMlib.configs.baseconfig import get_image_path
from SMlib.configs.guiconfig import get_shortcut
from SMlib.utils import programs
from SMlib.py3compat import is_text_string, to_text_string

# Note: How to redirect a signal from widget *a* to widget *b* ?
# ----
# It has to be done manually:
#  * typing 'SIGNAL("clicked()")' works
#  * typing 'signalstr = "clicked()"; SIGNAL(signalstr)' won't work
# Here is an example of how to do it:
# (self.listwidget is widget *a* and self is widget *b*)
#    self.connect(self.listwidget, SIGNAL('option_changed'),
#                 lambda *args: self.emit(SIGNAL('option_changed'), *args))


def get_icon(name, default=None, resample=False):
    """Return image inside a QIcon object
    default: default image name or icon
    resample: if True, manually resample icon pixmaps for usual sizes
    (16, 24, 32, 48, 96, 128, 256). This is recommended for QMainWindow icons 
    created from SVG images on non-Windows platforms due to a Qt bug (see 
    http://code.google.com/p/spyderlib/issues/detail?id=1314)."""
    if default is None:
        icon = QIcon(get_image_path(name))
    elif isinstance(default, QIcon):
        icon_path = get_image_path(name, default=None)
        icon = default if icon_path is None else QIcon(icon_path)
    else:
        icon = QIcon(get_image_path(name, default))
    if resample:
        icon0 = QIcon()
        for size in (16, 24, 32, 48, 96, 128, 256, 512):
            icon0.addPixmap(icon.pixmap(size, size))
        return icon0 
    else:
        return icon


def get_image_label(name, default="not_found.png"):
    """Return image inside a QLabel object"""
    label = QLabel()
    label.setPixmap(QPixmap(get_image_path(name, default)))
    return label


class MacApplication(QApplication):
    """Subclass to be able to open external files with our Mac app"""
    def __init__(self, *args):
        QApplication.__init__(self, *args)

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            fname = str(event.file())
            self.emit(SIGNAL('open_external_file(QString)'), fname)
        return QApplication.event(self, event)


def qapplication(translate=True):
    """Return QApplication instance
    Creates it if it doesn't already exist"""
    if sys.platform == "darwin" and 'Spyder.app' in __file__:
        SpyderApplication = MacApplication
    else:
        SpyderApplication = QApplication
    
    app = SpyderApplication.instance()
    if not app:
        # Set Application name for Gnome 3
        # https://groups.google.com/forum/#!topic/pyside/24qxvwfrRDs
        app = SpyderApplication(['Spyder'])
    if translate:
        install_translator(app)
    return app


def file_uri(fname):
    """Select the right file uri scheme according to the operating system"""
    if os.name == 'nt':
        # Local file
        if re.search(r'^[a-zA-Z]:', fname):
            return 'file:///' + fname
        # UNC based path
        else:
            return 'file://' + fname
    else:
        return 'file://' + fname


QT_TRANSLATOR = None
def install_translator(qapp):
    """Install Qt translator to the QApplication instance"""
    global QT_TRANSLATOR
    if QT_TRANSLATOR is None:
        qt_translator = QTranslator()
        if qt_translator.load("qt_"+QLocale.system().name(),
                      QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            QT_TRANSLATOR = qt_translator # Keep reference alive
    if QT_TRANSLATOR is not None:
        qapp.installTranslator(QT_TRANSLATOR)


def keybinding(attr):
    """Return keybinding"""
    ks = getattr(QKeySequence, attr)
    return QKeySequence.keyBindings(ks)[0]


def _process_mime_path(path, extlist):
    if path.startswith(r"file://"):
        if os.name == 'nt':
            # On Windows platforms, a local path reads: file:///c:/...
            # and a UNC based path reads like: file://server/share
            if path.startswith(r"file:///"): # this is a local path
                path=path[8:]
            else: # this is a unc path
                path = path[5:]
        else:
            path = path[7:]
    if osp.exists(path):
        if extlist is None or osp.splitext(path)[1] in extlist:
            return path


def mimedata2url(source, extlist=None):
    """
    Extract url list from MIME data
    extlist: for example ('.py', '.pyw')
    """
    pathlist = []
    if source.hasUrls():
        for url in source.urls():
            path = _process_mime_path(to_text_string(url.toString()), extlist)
            if path is not None:
                pathlist.append(path)
    elif source.hasText():
        for rawpath in to_text_string(source.text()).splitlines():
            path = _process_mime_path(rawpath, extlist)
            if path is not None:
                pathlist.append(path)
    if pathlist:
        return pathlist


def keyevent2tuple(event):
    """Convert QKeyEvent instance into a tuple"""
    return (event.type(), event.key(), event.modifiers(), event.text(),
            event.isAutoRepeat(), event.count())

    
def tuple2keyevent(past_event):
    """Convert tuple into a QKeyEvent instance"""
    return QKeyEvent(*past_event)


def restore_keyevent(event):
    if isinstance(event, tuple):
        _, key, modifiers, text, _, _ = event
        event = tuple2keyevent(event)
    else:
        text = event.text()
        modifiers = event.modifiers()
        key = event.key()
    ctrl = modifiers & Qt.ControlModifier
    shift = modifiers & Qt.ShiftModifier
    return event, text, key, ctrl, shift


def create_toolbutton(parent, text=None, shortcut=None, icon=None, tip=None,
                      toggled=None, triggered=None,
                      autoraise=True, text_beside_icon=False):
    """Create a QToolButton"""
    button = QToolButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        if is_text_string(icon):
            icon = get_icon(icon)
        button.setIcon(icon)
    if text is not None or tip is not None:
        button.setToolTip(text if tip is None else tip)
    if text_beside_icon:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    button.setAutoRaise(autoraise)
    if triggered is not None:
        QObject.connect(button, SIGNAL('clicked()'), triggered)
    if toggled is not None:
        QObject.connect(button, SIGNAL("toggled(bool)"), toggled)
        button.setCheckable(True)
    if shortcut is not None:
        button.setShortcut(shortcut)
    return button


def action2button(action, autoraise=True, text_beside_icon=False, parent=None):
    """Create a QToolButton directly from a QAction object"""
    if parent is None:
        parent = action.parent()
    button = QToolButton(parent)
    button.setDefaultAction(action)
    button.setAutoRaise(autoraise)
    if text_beside_icon:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    return button


def toggle_actions(actions, enable):
    """Enable/disable actions"""
    if actions is not None:
        for action in actions:
            if action is not None:
                action.setEnabled(enable)


def create_action(parent, text, shortcut=None, icon=None, tip=None,
                  toggled=None, triggered=None, data=None, menurole=None,
                  context=Qt.WindowShortcut):
    """Create a QAction"""
    action = QAction(text, parent)
    if triggered is not None:
        parent.connect(action, SIGNAL("triggered()"), triggered)
    if toggled is not None:
        parent.connect(action, SIGNAL("toggled(bool)"), toggled)
        action.setCheckable(True)
    if icon is not None:
        if is_text_string(icon):
            icon = get_icon(icon)
        action.setIcon(icon)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if data is not None:
        action.setData(data)
    if menurole is not None:
        action.setMenuRole(menurole)
    #TODO: Hard-code all shortcuts and choose context=Qt.WidgetShortcut
    # (this will avoid calling shortcuts from another dockwidget
    #  since the context thing doesn't work quite well with these widgets)
    action.setShortcutContext(context)
    return action


def add_shortcut_to_tooltip(action, context, name):
    """Add the shortcut associated with a given action to its tooltip"""
    action.setToolTip(action.toolTip() + ' (%s)' %
                      get_shortcut(context=context, name=name))


def add_actions(target, actions, insert_before=None):
    """Add actions to a menu"""
    previous_action = None
    target_actions = list(target.actions())
    if target_actions:
        previous_action = target_actions[-1]
        if previous_action.isSeparator():
            previous_action = None
    for action in actions:
        if (action is None) and (previous_action is not None):
            if insert_before is None:
                target.addSeparator()
            else:
                target.insertSeparator(insert_before)
        elif isinstance(action, QMenu):
            if insert_before is None:
                target.addMenu(action)
            else:
                target.insertMenu(insert_before, action)
        elif isinstance(action, QAction):
            if insert_before is None:
                target.addAction(action)
            else:
                target.insertAction(insert_before, action)
        previous_action = action


def get_item_user_text(item):
    """Get QTreeWidgetItem user role string"""
    return item.data(0, Qt.UserRole)


def set_item_user_text(item, text):
    """Set QTreeWidgetItem user role string"""
    item.setData(0, Qt.UserRole, text)


def create_bookmark_action(parent, url, title, icon=None, shortcut=None):
    """Create bookmark action"""
    return create_action( parent, title, shortcut=shortcut, icon=icon,
                          triggered=lambda u=url: programs.start_file(u) )


def create_module_bookmark_actions(parent, bookmarks):
    """
    Create bookmark actions depending on module installation:
    bookmarks = ((module_name, url, title), ...)
    """
    actions = []
    for key, url, title in bookmarks:
        if programs.is_module_installed(key):
            act = create_bookmark_action(parent, url, title)
            actions.append(act)
    return actions

        
def create_program_action(parent, text, name, icon=None, nt_name=None):
    """Create action to run a program"""
    if is_text_string(icon):
        icon = get_icon(icon)
    if os.name == 'nt' and nt_name is not None:
        name = nt_name
    path = programs.find_program(name)
    if path is not None:
        return create_action(parent, text, icon=icon,
                             triggered=lambda: programs.run_program(name))

        
def create_python_script_action(parent, text, icon, package, module, args=[]):
    """Create action to run a GUI based Python script"""
    if is_text_string(icon):
        icon = get_icon(icon)
    if programs.python_script_exists(package, module):
        return create_action(parent, text, icon=icon,
                             triggered=lambda:
                             programs.run_python_script(package, module, args))


class DialogManager(QObject):
    """
    Object that keep references to non-modal dialog boxes for another QObject,
    typically a QMainWindow or any kind of QWidget
    """
    def __init__(self):
        QObject.__init__(self)
        self.dialogs = {}
        
    def show(self, dialog):
        """Generic method to show a non-modal dialog and keep reference
        to the Qt C++ object"""
        for dlg in list(self.dialogs.values()):
            if to_text_string(dlg.windowTitle()) \
               == to_text_string(dialog.windowTitle()):
                dlg.show()
                dlg.raise_()
                break
        else:
            dialog.show()
            self.dialogs[id(dialog)] = dialog
            self.connect(dialog, SIGNAL('accepted()'),
                         lambda eid=id(dialog): self.dialog_finished(eid))
            self.connect(dialog, SIGNAL('rejected()'),
                         lambda eid=id(dialog): self.dialog_finished(eid))
        
    def dialog_finished(self, dialog_id):
        """Manage non-modal dialog boxes"""
        return self.dialogs.pop(dialog_id)
    
    def close_all(self):
        """Close all opened dialog boxes"""
        for dlg in list(self.dialogs.values()):
            dlg.reject()

        
def get_std_icon(name, size=None):
    """Get standard platform icon
    Call 'show_std_icons()' for details"""
    if not name.startswith('SP_'):
        name = 'SP_'+name
    icon = QWidget().style().standardIcon( getattr(QStyle, name) )
    if size is None:
        return icon
    else:
        return QIcon( icon.pixmap(size, size) )


def get_filetype_icon(fname):
    """Return file type icon"""
    ext = osp.splitext(fname)[1]
    if ext.startswith('.'):
        ext = ext[1:]
    return get_icon( "%s.png" % ext, get_std_icon('FileIcon') )


class ShowStdIcons(QWidget):
    """
    Dialog showing standard icons
    """
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        row_nb = 14
        cindex = 0
        for child in dir(QStyle):
            if child.startswith('SP_'):
                if cindex == 0:
                    col_layout = QVBoxLayout()
                icon_layout = QHBoxLayout()
                icon = get_std_icon(child)
                label = QLabel()
                label.setPixmap(icon.pixmap(32, 32))
                icon_layout.addWidget( label )
                icon_layout.addWidget( QLineEdit(child.replace('SP_', '')) )
                col_layout.addLayout(icon_layout)
                cindex = (cindex+1) % row_nb
                if cindex == 0:
                    layout.addLayout(col_layout)                    
        self.setLayout(layout)
        self.setWindowTitle('Standard Platform Icons')
        self.setWindowIcon(get_std_icon('TitleBarMenuButton'))


def show_std_icons():
    """
    Show all standard Icons
    """
    app = qapplication()
    dialog = ShowStdIcons(None)
    dialog.show()
    import sys
    sys.exit(app.exec_())

def from_qvariant(qobj=None, convfunc=None):
        '''
        api 1
        """Convert QVariant object to Python object"""
        assert callable(convfunc)
        if convfunc in (unicode, str):
            return convfunc(qobj.toString())
        elif convfunc is bool:
            return qobj.toBool()
        elif convfunc is int:
            return qobj.toInt()[0]
        elif convfunc is float:
            return qobj.toDouble()[0]
        else:
            return convfunc(qobj)
        '''
        return qobj
def to_qvariant(obj=None):  # analysis:ignore
        return obj
    
    
#===============================================================================
# Wrappers around QFileDialog static methods
# This is functions from qt.conpat.@shisj
#===============================================================================

def getexistingdirectory(parent=None, caption='', basedir='',
                         options=QFileDialog.ShowDirsOnly):
    """Wrapper around QtGui.QFileDialog.getExistingDirectory static method
    Compatible with PyQt >=v4.4 (API #1 and #2) and PySide >=v1.0"""
    # Calling QFileDialog static method
    if sys.platform == "win32":
        # On Windows platforms: redirect standard outputs
        _temp1, _temp2 = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = None, None
    try:
        result = QFileDialog.getExistingDirectory(parent, caption, basedir,
                                                  options)
    finally:
        if sys.platform == "win32":
            # On Windows platforms: restore standard outputs
            sys.stdout, sys.stderr = _temp1, _temp2
    if not isinstance(result, basestring):
        # PyQt API #1
        result = unicode(result)
    return result

def _qfiledialog_wrapper(attr, parent=None, caption='', basedir='',
                         filters='', selectedfilter='', options=None):
    if options is None:
        options = QFileDialog.Options(0)
    try:
        # PyQt <v4.6 (API #1)
        from spyderlib.qt.QtCore import QString
    except ImportError:
        # PySide or PyQt >=v4.6
        QString = None  # analysis:ignore
    tuple_returned = True
    try:
        # PyQt >=v4.6
        func = getattr(QFileDialog, attr+'AndFilter')
    except AttributeError:
        # PySide or PyQt <v4.6
        func = getattr(QFileDialog, attr)
        if QString is not None:
            selectedfilter = QString()
            tuple_returned = False
    
    # Calling QFileDialog static method
    if sys.platform == "win32":
        # On Windows platforms: redirect standard outputs
        _temp1, _temp2 = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = None, None
    try:
        result = func(parent, caption, basedir,
                      filters, selectedfilter, options)
    except TypeError:
        # The selectedfilter option (`initialFilter` in Qt) has only been 
        # introduced in Jan. 2010 for PyQt v4.7, that's why we handle here 
        # the TypeError exception which will be raised with PyQt v4.6
        # (see Issue 960 for more details)
        result = func(parent, caption, basedir, filters, options)
    finally:
        if sys.platform == "win32":
            # On Windows platforms: restore standard outputs
            sys.stdout, sys.stderr = _temp1, _temp2
            
    # Processing output
    if tuple_returned:
        # PySide or PyQt >=v4.6
        output, selectedfilter = result
    else:
        # PyQt <v4.6 (API #1)
        output = result
    if QString is not None:
        # PyQt API #1: conversions needed from QString/QStringList
        selectedfilter = unicode(selectedfilter)
        if isinstance(output, QString):
            # Single filename
            output = unicode(output)
        else:
            # List of filenames
            output = [unicode(fname) for fname in output]
            
    # Always returns the tuple (output, selectedfilter)
    return output, selectedfilter

def getopenfilename(parent=None, caption='', basedir='', filters='',
                    selectedfilter='', options=None):
    """Wrapper around QtGui.QFileDialog.getOpenFileName static method
    Returns a tuple (filename, selectedfilter) -- when dialog box is canceled,
    returns a tuple of empty strings
    Compatible with PyQt >=v4.4 (API #1 and #2) and PySide >=v1.0"""
    return _qfiledialog_wrapper('getOpenFileName', parent=parent,
                                caption=caption, basedir=basedir,
                                filters=filters, selectedfilter=selectedfilter,
                                options=options)

def getopenfilenames(parent=None, caption='', basedir='', filters='',
                     selectedfilter='', options=None):
    """Wrapper around QtGui.QFileDialog.getOpenFileNames static method
    Returns a tuple (filenames, selectedfilter) -- when dialog box is canceled,
    returns a tuple (empty list, empty string)
    Compatible with PyQt >=v4.4 (API #1 and #2) and PySide >=v1.0"""
    return _qfiledialog_wrapper('getOpenFileNames', parent=parent,
                                caption=caption, basedir=basedir,
                                filters=filters, selectedfilter=selectedfilter,
                                options=options)

def getsavefilename(parent=None, caption='', basedir='', filters='',
                    selectedfilter='', options=None):
    """Wrapper around QtGui.QFileDialog.getSaveFileName static method
    Returns a tuple (filename, selectedfilter) -- when dialog box is canceled,
    returns a tuple of empty strings
    Compatible with PyQt >=v4.4 (API #1 and #2) and PySide >=v1.0"""
    return _qfiledialog_wrapper('getSaveFileName', parent=parent,
                                caption=caption, basedir=basedir,
                                filters=filters, selectedfilter=selectedfilter,
                                options=options)
    
if __name__ == "__main__":
    show_std_icons()
    
