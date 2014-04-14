"""
"""



__version__ = "0.0.1"
import os

os.environ.setdefault('QT_API', 'pyqt')
assert os.environ['QT_API'] in ('pyqt', 'pyside')

API = os.environ['QT_API']
API_NAME = {'pyqt': 'PyQt4', 'pyside': 'PySide'}[API]


def get_versions():
    """Get version information for components used by Spyder"""
    import sys
    import os.path as osp
    import platform
    import SMlib
    from SMlib.utils import vcs
    from PyQt4 import QtCore
    spyderpath = SMlib.__path__[0]
    full, short, branch = vcs.get_hg_revision(osp.dirname(spyderpath))
    revision = None
    if full:
        revision = '%s:%s' % (full, short)
    if not sys.platform == 'darwin':  # To avoid a crash with our Mac app
        system = platform.system()
    else:
        system = 'Darwin'
    return {
        'spyder': SMlib.__version__,
        'python': platform.python_version(),  # "2.7.3"
        'bitness': 64 if sys.maxsize > 2**32 else 32,
        'qt': QtCore.QT_VERSION_STR,
        'qt_api': API_NAME,      # PySide or PyQt4
        'qt_api_ver': QtCore.QT_VERSION_STR,
        'system': system,   # Linux, Windows, ...
        'revision': revision,  # '9fdf926eccce+:2430+'
    }