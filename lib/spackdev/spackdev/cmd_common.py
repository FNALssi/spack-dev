#!/usr/bin/env python

import os.path
import sys
from spack_import import tty
from misc import external_cmd

def stage(packages):
    for package in packages:
        tty.msg('staging '  + package)
        stage_py_filename = os.path.join('spackdev', package, 'bin', 'stage.py')
        retval, output = external_cmd([stage_py_filename])

