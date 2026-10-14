import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources'))
from lib.runtime import context_add
if __name__ == '__main__':
    context_add(getattr(sys, 'listitem', None))
