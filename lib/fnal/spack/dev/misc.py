#!/usr/bin/env python

import sys
import os
import ast
import time
from llnl.util import tty

if sys.version_info[0] > 2 and sys.version_info[1] > 2:
    import shutil
else:
    from distutils import spawn

def read_packages_file():
    packages_filename = os.path.join('spackdev-aux', 'packages.sd')
    with open(packages_filename, 'r') as f:
        first_line = f.readline().rstrip()
        if first_line.find('[') > -1:
            tty.die('packages.sd in obsolete (unsafe) format: please initialize a new spackdev area.')
        requesteds = first_line.split()
        additional = f.readline().rstrip().split()
        install_args = f.readline().rstrip()
    return requesteds, additional, install_args

def which(executable):
    if sys.version_info[0] > 2 and sys.version_info[1] > 2:
        return shutil.which(executable)
    else:
        return spawn.find_executable(executable)
