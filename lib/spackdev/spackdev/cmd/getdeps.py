#!/usr/bin/env python

import argparse
from spackdev import install_dependencies
from spackdev.spack_import import tty

description  = 'install missing dependencies of packages in a SpackDev area'

def setup_parser(subparser):
    pass

def getdeps(parser, args):
    install_dependencies()
