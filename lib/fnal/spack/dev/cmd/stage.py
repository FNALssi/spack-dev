import argparse
from llnl.util import tty

import fnal.spack.dev as dev

description  = 'stage packages in a spackdev area'


def setup_parser(subparser):
    subparser.add_argument('packages', nargs='*',
                           help="specs of packages to stage; if empty stage all packages")


def validate_args(packages, all_packages):
    for package in packages:
        if not package in all_packages:
            tty.die("stage: '{0}' is not in the list of SpackDev area packages ({1})"
                    .format(package, all_packages))


def stage(parser, args):
    requested, additional, deps, install_specs = dev.cmd.read_package_info()
    all_packages = requested + additional

    validate_args(args.packages, all_packages)
    if len(args.packages) == 0:
        packages = all_packages
    else:
        packages = args.packages

    for package in packages:
        tty.msg('staging ' + package)
        dev.cmd.stage_package(package,
                              dev.cmd.get_package_spec(package, install_specs))
