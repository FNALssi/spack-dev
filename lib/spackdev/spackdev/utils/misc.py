#!/usr/bin/env python

from commands import getstatusoutput

def spack_cmd(args):
    argstr = " ".join(args)
    cmd = "spack " + argstr
    print "spack_cmd = '{}'".format(cmd)
    return getstatusoutput(cmd)

