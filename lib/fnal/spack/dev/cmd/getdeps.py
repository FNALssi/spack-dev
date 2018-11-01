#!/usr/bin/env python

import argparse
from fnal.spack.dev import install_dependencies
from llnl.util import tty

description  = 'install missing dependencies of packages in a SpackDev area'

def setup_parser(subparser):
    pass

def getdeps(parser, args):
    install_dependencies()
