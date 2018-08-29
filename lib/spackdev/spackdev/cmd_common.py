#!/usr/bin/env python

import os
import re
import shutil
import sys
from spack_import import tty
from misc import spack_cmd, read_packages_file
from six.moves import shlex_quote as cmd_quote
from six.moves import cPickle


def bootstrap_environment():
    if 'SPACKDEV_BASE' not in os.environ:
        env_file_name = os.path.join('spackdev-aux', 'env.pickle')
        if os.path.exists(env_file_name):
            os.environ.update(sanitized_environment
                              (environment_from_pickle(env_file_name)))
        else:
            tty.die('unable to find spackdev area: please source spackdev-aux/env.sh or execute from parent of spackdev-aux/')


def install_dependencies(**kwargs):
    if 'install_args' in kwargs:
        install_args = kwargs['install_args']
        dev_packages = kwargs['dev_packages']
    else:
        (requested, additional, install_args) = read_packages_file()
        dev_packages = requested + additional

    tty.msg('requesting spack install of dependencies for: {0}'
            .format(' '.join(dev_packages)))
    excludes = ','.join(dev_packages)
    if len(install_args) >0:
        retval, output = spack_cmd(['install',
#                                '--implicit',
                                install_args])
    else: 
        retval, output = spack_cmd(['info',' '.join(dev_packages)])
    return retval, output


def srcs_topdir():
    bootstrap_environment()
    result = os.path.join(os.environ['SPACKDEV_BASE'], 'srcs')
    return result


def stage_package(package):
    topdir = srcs_topdir()
    if not os.path.exists(topdir):
        os.mkdir(topdir)
    if os.path.exists(os.path.join(topdir, package)):
        tty.msg('stage: directory "{0}" exists: skipping'.format(package))
        return
    tty.msg('staging '  + package)
    stage_tmp = '{0}/spackdev-aux/.tmp'.format(os.environ['SPACKDEV_BASE'])
    retval, output = spack_cmd(['stage', '-p', stage_tmp, package])
    if retval != 0:
        tty.die('staging {0} failed'.format(package))
    shutil.move('{0}/{1}'.format(stage_tmp, package), '{0}/'.format(topdir))
    os.remove(stage_tmp)


def stage_packages(packages):
    for package in packages:
        stage_package(package)


def environment_from_pickle(path):
    environment = cPickle.load(open(path, 'rb'))
    assert(type(environment) == dict)
    return environment


# Deal with possibly quoted values, with optional leading export
# keyword or trailing statement.
var_finder\
    = re.compile(r'^(?:export\s+)?(?P<var>[A-Za-z_][A-Za-z_0-9()]*)=(?P<val>(?P<sp>\')?.*?(?(sp)\')(?:;\s+export\s+\1;?)?$)',
                 re.DOTALL | re.MULTILINE)
def environment_from_string(env_string):
    environment=dict((match.group('var'), match.group('val')) for
                     match in var_finder.finditer(package_env))
    return environment


# Variable blacklist.
var_blacklist\
    = re.compile(r'(?:.*AUTH.*|.*SESSION.*|DISPLAY$|HOME$|KONSOLE_|PROMPT_COMMAND$|PS\d|(?:OLD)?PWD$|SHLVL$|SSH_|TERM$|USER$|WINDOWID$|XDG_|_$)')
# Variable whitelist.
var_whitelist = re.compile(r'SPACK(?:DEV)?_')
def sanitized_environment(environment, drop_unchanged=False):
    return dict((var, val) for (var, val) in environment.iteritems() if var_whitelist.match(var) or not
            (var_blacklist.match(var) or
             (drop_unchanged and var in os.environ and
              val == cmd_quote(os.environ[var]))))
