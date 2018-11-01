#!/usr/bin/env python

import argparse
from fnal.spack.dev import read_packages_file
import re
import glob
import os
import copy
import shutil
import sys
import ast

description = "describe a spackdev area"


def setup_parser(subparser):
    subparser.add_argument('pathname', nargs=argparse.REMAINDER,
                           help="pathname of SpackDev area")
    # subparser.add_argument('-s', '--no-stage', action='store_true', dest='no_stage',
    #     help="do not stage packages")

def info(parser, args):
    if args.pathname:
        dir = args.pathname
    else:
        dir = '.'
    if (not os.path.exists(dir)):
        sys.stderr.write('spack info: no such pathname "' + dir + '"\n')
        sys.exit(1)
    os.chdir(dir)
    if (not os.path.exists('spackdev-aux')) :
        sys.stderr.write('spackdev info: ' + dir + ' is not a SpackDev area\n')
        sys.exit(1)

    requested, additional, install_args =  read_packages_file()
    print('requested packages:')
    for package in requested:
        print('    ' + package)
    if len(additional) > 0:
        print('additional dependent packages:')
        for package in additional:
            print('    ' + package)
