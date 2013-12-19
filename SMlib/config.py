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

DEFAULTS = [
            ('main',
             {
              'window/size': (1260, 740),
              'window/position': (10, 10),
              'window/is_maximized': False,
              'window/is_fullscreen': False,
              }
             )
            ]
CONF = UserConfig('SMGui', defaults=DEFAULTS, load=True, version= __version__,
                  subfolder=SUBFOLDER, backup=True, raw_mode=True)
if __name__ == "__main__":
    print SUBFOLDER
    