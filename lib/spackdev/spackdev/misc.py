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

def spack_cmd(args):
    argstr = ' '.join(args)
    cmd = "spack " + argstr
    # print "jfa spack_cmd = '{}'".format(cmd)
    t0 = time.time()
    status, output = getstatusoutput(cmd)
    t1 = time.time()
    tty.verbose('spack_cmd: {} {}s'.format(args[0], t1 - t0))
    if status != 0:
        tty.error('spack command output:\n' + output)
        tty.die('spack command "{}" failed with return value {}'\
                .format(cmd, status))
    # print 'spack_cmd:', args[0], t1 - t0, 's'
    return status, output

def external_cmd(args):
    cmd = ' '.join(args)
    status, output = getstatusoutput(cmd)
    if status != 0:
        sys.stderr.write('command "{}" failed\n'.format(cmd))
        sys.stderr.write('output:\n')
        sys.stderr.write(output + '\n')
    return status, output

def read_packages_file():
    packages_filename = os.path.join('spackdev', 'packages.sd')
    with open(packages_filename, 'r') as f:
        requesteds = ast.literal_eval(f.readline())
        additional = ast.literal_eval(f.readline())
    return requesteds, additional

def which(executable):
    if sys.version_info[0] > 2 and sys.version_info[1] > 2:
        return shutil.which(executable)
    else:
        return spawn.find_executable(executable)
