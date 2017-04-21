#!/usr/bin/env python

import argparse
from spackdev import install_dependencies
from spackdev import read_packages_file
from spackdev.spack_import import tty

description  = 'install missing depenendencies of packages in a SpackDev area'

def setup_parser(subparser):
    pass

def getdeps(parser, args):
    requesteds, additional = read_packages_file()
    all_packages = requesteds + additional

    tty.msg('installing dependencies for ' + ' '.join(all_packages))
    install_dependencies(all_packages)