#!/usr/bin/env python

from __future__ import print_function

import argparse
from spackdev import External_repo, Packages_yaml
description = "describe a spackdev area"


def setup_parser(subparser):
    pass
    # subparser.add_argument('pathname', nargs=argparse.REMAINDER,
    #                        help="pathname of SpackDev area")
    # subparser.add_argument('-s', '--no-stage', action='store_true', dest='no_stage',
    #     help="do not stage packages")

def findext(parser, args):
    external_repo = External_repo()
    packages_yaml = Packages_yaml()
    packages_yaml.write_file(external_repo.all_external_packages())