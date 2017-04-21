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

def stage_package(package):
    tty.debug('jfa getcwd() = {}'.format(os.getcwd()))
    if os.path.exists(os.path.join('.', package)):
        tty.die('stage: directory "{}" exists.'.format(package))
    tty.msg('staging '  + package)
    stage_py_filename = os.path.join('spackdev', package, 'bin', 'stage.py')
    retval, output = external_cmd([stage_py_filename])
    if retval != 0:
        tty.die('staging {} failed'.format(package))

def stage_packages(packages):
    for package in packages:
        stage_package(package)