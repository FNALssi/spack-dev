#!/usr/bin/env python

import argparse
from spackdev import utils
import re
import glob
import os
import copy
import shutil
import sys
import ast

description = "describe a spackdev area"


def read_packages_file():
    packages_filename = os.path.join('spackdev', 'packages.sd')
    with open(packages_filename, 'r') as f:
        requesteds = ast.literal_eval(f.readline())
        additional = ast.literal_eval(f.readline())
    return requesteds, additional


def setup_parser(subparser):
    subparser.add_argument('pathname',
                           help="pathname of SpackDev area")
    # subparser.add_argument('-s', '--no-stage', action='store_true', dest='no_stage',
    #     help="do not stage packages")

def info(parser, args):
    dir = args.pathname
    if (not os.path.exists(dir)):
        sys.stderr.write('spack info: no such pathname "' + dir + '"\n')
        sys.exit(1)
    os.chdir(dir)
    if (not os.path.exists('spackdev')) :
        sys.stderr.write('spackdev info: ' + dir + ' is not a SpackDev area\n')
        sys.exit(1)

    requesteds, additional =  read_packages_file()
    print('requested packages:')
    for package in requesteds:
        print('    ' + package)
    if len(additional) > 0:
        print('additional dependent packages:')
        for package in additional:
            print('    ' + package)
