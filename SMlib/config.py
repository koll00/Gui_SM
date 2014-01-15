"""
SMGui configuration options

it can be used to quickly load a user config file
"""


import sys,os 
sys.path.append('..'+ os.path.sep)

import os.path as osp
from SMlib.configs import __version__

from SMlib.configs.userconfig import UserConfig
from SMlib.configs.baseconfig import SUBFOLDER, CHECK_ALL, EXCLUDED_NAMES

SANS_SERIF = ['Sans Serif', 'DejaVu Sans', 'Bitstream Vera Sans',
              'Bitstream Charter', 'Lucida Grande', 'MS Shell Dlg 2',
              'Calibri', 'Verdana', 'Geneva', 'Lucid', 'Arial',
              'Helvetica', 'Avant Garde', 'Times', 'sans-serif']

MONOSPACE = ['Monospace', 'DejaVu Sans Mono', 'Consolas', 'Monaco',
             'Bitstream Vera Sans Mono', 'Andale Mono', 'Liberation Mono',
             'Courier New', 'Courier', 'monospace', 'Fixed', 'Terminal']
if sys.platform == 'darwin':
    BIG = MEDIUM = SMALL = 12
elif os.name == 'nt':
    BIG = 12    
    MEDIUM = 10
    SMALL = 9
else:
    BIG = 12    
    MEDIUM = 9
    SMALL = 9
    
DEFAULTS = [
            ('main',
             {
              'window/size': (1260, 740),
              'window/position': (10, 10),
              'window/prefs_dialog_size': (745, 411),
              'window/is_maximized': False,
              'window/is_fullscreen': False,
              'vertical_dockwidget_titlebars': False,
              'vertical_tabs': False,
              }
             ),
            ('ipython_console',
             {
              'font/family': MONOSPACE,
              'font/size': MEDIUM,
              'font/italic': False,
              'font/bold': False,
              'show_banner': True,
              'use_gui_completion': True,
              'use_pager': True,
              'show_calltips': False,
              'ask_before_closing': True,
              'object_inspector': True,
              'buffer_size': 10000,
              'pylab': True,
              'pylab/autoload': True,
              'pylab/backend': 0,
              'pylab/inline/figure_format': 0,
              'pylab/inline/resolution': 72,
              'pylab/inline/width': 6,
              'pylab/inline/height': 4,
              'startup/run_lines': '',
              'startup/use_run_file': False,
              'startup/run_file': '',
              'open_ipython_at_startup': False,
              'greedy_completer': False,
              'autocall': 0,
              'symbolic_math': False,
              'in_prompt': '',
              'out_prompt': ''
              })
            ]
CONF = UserConfig('SMGui', defaults=DEFAULTS, load=True, version= __version__,
                  subfolder=SUBFOLDER, backup=True, raw_mode=True)
if __name__ == "__main__":
    print SUBFOLDER
    