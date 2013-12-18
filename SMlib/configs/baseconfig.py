"""
SMGui base configuration management

As opposed to SMlib/config.py, this configuration script deals 
exclusively with non-GUI features configuration only
(in other words, we won't import any PyQt object here, avoiding any 
sip API incompatibility issue in SMlib's non-gui modules)
"""

from __future__ import print_function

import os.path as osp
import os
import sys
sys.path.append('..\\..\\')
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
DEBUG = _get_debug_env()

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

# Variable explorer display / check all elements data types for sequences:
# (when saving the variable explorer contents, check_all is True,
#  see widgets/externalshell/namespacebrowser.py:NamespaceBrowser.save_data)
CHECK_ALL = False #XXX: If True, this should take too much to compute...

EXCLUDED_NAMES = ['nan', 'inf', 'infty', 'little_endian', 'colorbar_doc',
                  'typecodes', '__builtins__', '__main__', '__doc__', 'NaN',
                  'Inf', 'Infinity', 'sctypes', 'rcParams', 'rcParamsDefault',
                  'sctypeNA', 'typeNA', 'False_', 'True_',]
