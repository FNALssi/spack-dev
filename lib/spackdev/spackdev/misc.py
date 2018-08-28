#!/usr/bin/env python

from commands import getstatusoutput
import sys
import os
import ast
import time
from spack_import import tty

if sys.version_info[0] > 2 and sys.version_info[1] > 2:
    import shutil
else:
    from distutils import spawn

def spack_cmd(args, **kwargs):
    argstr = ' '.join(args)
    cmd = "spack " + argstr
    # print "jfa spack_cmd = '{}'".format(cmd)
    t0 = time.time()
    status, output = getstatusoutput(cmd)
    t1 = time.time()
    tty.verbose('spack_cmd: {0} {1}s'.format(args[0], str(t1 - t0)))
    if status != 0 and not \
       ('ignore_errors' in kwargs and kwargs['ignore_errors']):
        tty.error('spack command output:\n' + output)
        tty.die('spack command "{0}" failed with return value {1}'\
                .format(cmd, status))
    return status, output

def external_cmd(args, **kwargs):
    cmd = ' '.join(args)
    status, output = getstatusoutput(cmd)
    if status != 0 and not \
       ('ignore_errors' in kwargs and kwargs['ignore_errors']):
        tty.error('command output:\n' + output)
        tty.die('command "{0}" failed with return value {1}'\
                .format(cmd, status))
    return status, output

def read_packages_file():
    packages_filename = os.path.join('spackdev', 'packages.sd')
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
