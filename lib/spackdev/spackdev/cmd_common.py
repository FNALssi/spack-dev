#!/usr/bin/env python

import os.path
import sys
from spack_import import tty
from misc import external_cmd, spack_cmd

def install_dependencies(packages):
    tty.msg('requesting spack install of dependent packages')
    excludes = ','.join(packages)
    install_packages = ' '.join(packages)
    retval, output = spack_cmd(['install', '--only dependencies',
                                '--exclude', excludes, install_packages])
    return retval, output

def stage(packages):
    for package in packages:
        tty.msg('staging '  + package)
        stage_py_filename = os.path.join('spackdev', package, 'bin', 'stage.py')
        retval, output = external_cmd([stage_py_filename])
        if retval != 0:
            tty.die('staging {} failed'.format(package))

