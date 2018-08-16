#!/usr/bin/env python
from __future__ import print_function

import argparse
import copy
import os
from spackdev import environment_from_pickle, sanitized_environment,\
    bootstrap_environment


description = "run a command in the build environment of a spackdev package, or start a shell in same."


def load_environment(package):
    package_env_file_name\
        = os.path.join(os.environ['SPACKDEV_BASE'],
                       'spackdev', package, 'env', 'env.pickle')
    environment = copy.copy(os.environ)
    environment.update(sanitized_environment
                       (environment_from_pickle(package_env_file_name)))
    return environment


def setup_parser(subparser):
    subparser.add_argument('package',
                           help='package for which to initialize environment.')
    subparser.add_argument('cmd', nargs=argparse.REMAINDER,
                           help='Command and arguments to execute (default is to start a shell)')


def env(parser, args):
    bootstrap_environment()
    if not args.cmd:
        shell = os.environ['SPACK_SHELL']
        if not shell:
            shell = os.environ['SHELL']
        args.cmd = [ shell ]
    environment = load_environment(args.package)
    os.execvpe(args.cmd[0], args.cmd, environment)
