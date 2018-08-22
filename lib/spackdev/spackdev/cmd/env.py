#!/usr/bin/env python
from __future__ import print_function

import argparse
import copy
import os
from spackdev import environment_from_pickle, sanitized_environment,\
    bootstrap_environment
from spackdev.spack_import import tty

description = "run a command in the build environment of a spackdev package, or start a shell in same."


def load_environment(package):
    package_env_file_name\
        = os.path.join(os.environ['SPACKDEV_BASE'],
                       'spackdev', package, 'env', 'env.pickle')
    if not os.path.exists(package_env_file_name):
        tty.die('unable to find environment for {0}: not a package being developed?'.format(package))
    environment = copy.copy(os.environ)
    environment.update(sanitized_environment
                       (environment_from_pickle(package_env_file_name)))
    return environment


prompt_splitter = re.compile(r'(.*?)([#\$]\s*)?$')
def process_rc_options(args_cli):
    if args_cli.cd:
        os.chdir(os.path.join(os.environ['SPACKDEV_BASE'],
                              'build', args_cli.package))


def setup_parser(subparser):
    subparser.add_argument('package',
                           help='package for which to initialize environment.')
    subparser.add_argument('cmd', nargs=argparse.REMAINDER,
                           help='Command and arguments to execute (default is to start a shell)')
    subparser.add_argument('--cd', action='store_true', default=False,
                           help='Execute the command in the build directory for the specified package')


def env(parser, args):
    bootstrap_environment()
    if not args.cmd:
        shell = os.environ['SPACK_SHELL']
        if not shell:
            shell = os.environ['SHELL']
        args.cmd = [ shell ]
    environment = load_environment(args.package)
    process_rc_options(args)
    tty.msg('executing {0} in environment for package {1}'.
            format(' '.join(args.cmd), args.package))
    os.execvpe(args.cmd[0], args.cmd, environment)
