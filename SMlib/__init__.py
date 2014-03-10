"""
"""



__version__ = "0.0.1"



def get_versions():
    """Get version information for components used by Spyder"""
    import sys
    import os.path as osp
    import platform
    import spyderlib
    from spyderlib.utils import vcs
    spyderpath = spyderlib.__path__[0]
    full, short, branch = vcs.get_hg_revision(osp.dirname(spyderpath))
    revision = None
    if full:
        revision = '%s:%s' % (full, short)
    if not sys.platform == 'darwin':  # To avoid a crash with our Mac app
        system = platform.system()
    else:
        system = 'Darwin'
    return {
        'spyder': spyderlib.__version__,
        'python': platform.python_version(),  # "2.7.3"
        'bitness': 64 if sys.maxsize > 2**32 else 32,
        'qt': spyderlib.qt.QtCore.__version__,
        'qt_api': spyderlib.qt.API_NAME,      # PySide or PyQt4
        'qt_api_ver': spyderlib.qt.__version__,
        'system': system,   # Linux, Windows, ...
        'revision': revision,  # '9fdf926eccce+:2430+'
    }