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
    print('jfa: findext start')
    external_repo = External_repo()
    print('jfa: external_repo.all_external_names() =', external_repo.all_external_names())
    for pkg in external_repo.all_external_names():
        print('{}:'.format(pkg))
        external_repo.get_pkg_class(pkg)().find()

    print('jfa: reading packages.yaml:')
    packages_yaml = Packages_yaml()
    print('jfa: pre_lines:')
    for line in packages_yaml.pre_lines:
        print(line.rstrip())
    print('jfa: post_lines:')
    for line in packages_yaml.post_lines:
        print(line.rstrip())
    packages_yaml.write_file(external_repo.all_external_packages())