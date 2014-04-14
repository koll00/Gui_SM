"""
SMGui base configuration management

As opposed to SMlib/config.py, this configuration script deals 
exclusively with non-GUI features configuration only
(in other words, we won't import any PyQt object here, avoiding any 
sip API incompatibility issue in SMlib's non-gui modules)
"""

from __future__ import print_function

import os.path as osp
import sys,os 
sys.path.append('..'+ os.path.sep + '..' + os.path.sep)

from SMlib.configs import __version__


#==============================================================================
# Only for development
#==============================================================================
# To activate/deactivate certain things for development
# SPYDER_DEV is (and *only* have to be) set in bootstrap.py
DEV = os.environ.get('SPYDER_DEV')

# For testing purposes
# SPYDER_TEST can be set using the --test option of bootstrap.py
TEST = os.environ.get('SPYDER_TEST')


#==============================================================================
# Debug helpers
#==============================================================================
STDOUT = sys.stdout
STDERR = sys.stderr
def _get_debug_env():
    debug_env = os.environ.get('SPYDER_DEBUG', '')
    if not debug_env.isdigit():
        debug_env = bool(debug_env)
    return int(debug_env)    
#DEBUG = _get_debug_env()
DEBUG = 1

def debug_print(message):
    """Output debug messages to stdout"""
    if DEBUG:
        ss = STDOUT
        print(message, file=ss)


#==============================================================================
# Configuration paths
#==============================================================================
if TEST is None:
#    SUBFOLDER = '.SMGui%s' % __version__.split('.')[0]
    SUBFOLDER = '.SMGui%s' % __version__
else:
    SUBFOLDER = 'SMGui_test'

def get_conf_path(filename=None):
    """Return absolute path for configuration file with specified filename"""
    if TEST is None:
        from SMlib.configs import userconfig
        conf_dir = osp.join(userconfig.get_home_dir(), SUBFOLDER)
    else:
         import tempfile
         conf_dir = osp.join(tempfile.gettempdir(), SUBFOLDER)
    if not osp.isdir(conf_dir):
        os.mkdir(conf_dir)
    if filename is None:
        return conf_dir
    else:
        return osp.join(conf_dir, filename)
        

def get_module_path(modname):
    """Return module *modname* base path"""
    return osp.abspath(osp.dirname(sys.modules[modname].__file__))


def get_module_data_path(modname, relpath=None, attr_name='DATAPATH'):
    """Return module *modname* data path
    Note: relpath is ignored if module has an attribute named *attr_name*
    
    Handles py2exe/cx_Freeze distributions"""
    datapath = getattr(sys.modules[modname], attr_name, '')
    if datapath:
        return datapath
    else:
        datapath = get_module_path(modname)
        parentdir = osp.join(datapath, osp.pardir)
        if osp.isfile(parentdir):
            # Parent directory is not a directory but the 'library.zip' file:
            # this is either a py2exe or a cx_Freeze distribution
            datapath = osp.abspath(osp.join(osp.join(parentdir, osp.pardir),
                                            modname))
        if relpath is not None:
            datapath = osp.abspath(osp.join(datapath, relpath))
        return datapath

def get_module_source_path(modname, basename=None):
    """Return module *modname* source path
    If *basename* is specified, return *modname.basename* path where 
    *modname* is a package containing the module *basename*
    
    *basename* is a filename (not a module name), so it must include the
    file extension: .py or .pyw
    
    Handles py2exe/cx_Freeze distributions"""
    srcpath = get_module_path(modname)
    parentdir = osp.join(srcpath, osp.pardir)
    if osp.isfile(parentdir):
        # Parent directory is not a directory but the 'library.zip' file:
        # this is either a py2exe or a cx_Freeze distribution
        srcpath = osp.abspath(osp.join(osp.join(parentdir, osp.pardir),
                                       modname))
    if basename is not None:
        srcpath = osp.abspath(osp.join(srcpath, basename))
    return srcpath

# Variable explorer display / check all elements data types for sequences:
# (when saving the variable explorer contents, check_all is True,
#  see widgets/externalshell/namespacebrowser.py:NamespaceBrowser.save_data)
CHECK_ALL = False #XXX: If True, this should take too much to compute...

EXCLUDED_NAMES = ['nan', 'inf', 'infty', 'little_endian', 'colorbar_doc',
                  'typecodes', '__builtins__', '__main__', '__doc__', 'NaN',
                  'Inf', 'Infinity', 'sctypes', 'rcParams', 'rcParamsDefault',
                  'sctypeNA', 'typeNA', 'False_', 'True_',]

#==============================================================================
# Image path list
#==============================================================================

IMG_PATH = []
def add_image_path(path):
    if not osp.isdir(path):
        return
    global IMG_PATH
    IMG_PATH.append(path)
    for _root, dirs, _files in os.walk(path):
        for dir in dirs:
            IMG_PATH.append(osp.join(path, dir))


add_image_path(get_module_data_path('SMlib', relpath='icons'))

def get_image_path(name, default="not_found.png"):
    """Return image absolute path"""
    for img_path in IMG_PATH:
        full_path = osp.join(img_path, name)
        if osp.isfile(full_path):
            return osp.abspath(full_path)
    if default is not None:
        #return osp.abspath(osp.join(img_path, default))
        return osp.abspath(osp.join(name, default))

#==============================================================================
# Translations
#==============================================================================
def get_translation(modname, dirname=None):
    """Return translation callback for module *modname*"""
    if dirname is None:
        dirname = modname
    locale_path = get_module_data_path(dirname, relpath="locale",
                                       attr_name='LOCALEPATH')
    # fixup environment var LANG in case it's unknown
    if "LANG" not in os.environ:
        import locale
        lang = locale.getdefaultlocale()[0]
        if lang is not None:
            os.environ["LANG"] = lang
    import gettext
    try:
        _trans = gettext.translation(modname, locale_path, codeset="utf-8")
        lgettext = _trans.lgettext
        def translate_gettext(x):
            if isinstance(x, unicode):
                x = x.encode("utf-8")
            return unicode(lgettext(x), "utf-8")
        return translate_gettext
    except IOError, _e:  # analysis:ignore
        #print "Not using translations (%s)" % _e
        def translate_dumb(x):
            if not isinstance(x, unicode):
                return unicode(x, "utf-8")
            return x
        return translate_dumb

# Translation callback
_ = get_translation("SMlib")

#==============================================================================
# Namespace Browser (Variable Explorer) configuration management
#==============================================================================

def get_supported_types():
    """
    Return a dictionnary containing types lists supported by the 
    namespace browser:
    dict(picklable=picklable_types, editable=editables_types)
         
    See:
    get_remote_data function in SMlib/widgets/externalshell/monitor.py
    get_internal_shell_filter method in namespacebrowser.py
    
    Note:
    If you update this list, don't forget to update doc/variablexplorer.rst
    """
    from datetime import date
    editable_types = [int, long, float, list, dict, tuple, str, unicode, date]
    try:
        from numpy import ndarray, matrix
        editable_types += [ndarray, matrix]
    except ImportError:
        pass
    picklable_types = editable_types[:]
    try:
        from SMlib.pil_patch import Image
        editable_types.append(Image.Image)
    except ImportError:
        pass
    return dict(picklable=picklable_types, editable=editable_types)

if __name__ == '__main__':
    add_image_path(get_module_data_path('SMlib', relpath='icons'))
