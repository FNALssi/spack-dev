#!/usr/bin/env python

from commands import getstatusoutput
import sys
import time
from spack_import import tty

def spack_cmd(args):
    argstr = ' '.join(args)
    cmd = "spack " + argstr
    # print "jfa spack_cmd = '{}'".format(cmd)
    t0 = time.time()
    status, output = getstatusoutput(cmd)
    t1 = time.time()
    tty.verbose('spack_cmd: {} {}s'.format(args[0], t1 - t0))
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
