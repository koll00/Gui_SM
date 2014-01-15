'''
'''

import sys,os 
sys.path.append('..'+ os.path.sep)

from SMlib import SMGui as app

def main():
    app.run()
    
if __name__ == '__main__':
    main()
    print sys.modules['SMlib']