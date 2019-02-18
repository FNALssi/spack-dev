import os
import re
import shutil
import sys
from llnl.util import tty
from misc import read_packages_file
from six.moves import shlex_quote as cmd_quote
from six.moves import cPickle
import spack.cmd

def bootstrap_environment():
    if 'SPACKDEV_BASE' not in os.environ:
        env_file_name = os.path.join('spackdev-aux', 'env.pickle')
        if os.path.exists(env_file_name):
            os.environ.update(sanitized_environment
                              (environment_from_pickle(env_file_name)))
        else:
            tty.die('unable to find spackdev area: please source spackdev-aux/env.sh or execute from parent of spackdev-aux/')


def get_package_spec(package, specs):
    return reduce(lambda a, b : a if package in a else b, specs, {})[package]


def install_dependencies(**kwargs):
    if 'dep_specs' in kwargs:
        dep_specs = kwargs['dep_specs']
        dev_packages = kwargs['dev_packages']
    else:
        # Concretization is necessary.
        (requested, additional, deps, install_specs) = read_packages_file()
        dev_packages = requested + additional
        dep_specs = [ get_package_spec(dep, install_specs) for dep in deps ]

    tty.msg('requesting spack install of dependencies for: {0}'
            .format(' '.join(dev_packages)))
    for dep in dep_specs:
        tty.debug('installing dependency {0}'.format(dep.name))
        dep.package.do_install()


def srcs_topdir():
    bootstrap_environment()
    result = os.path.join(os.environ['SPACKDEV_BASE'], 'srcs')
    return result


def stage_package(package, spec):
    topdir = srcs_topdir()
    if not os.path.exists(topdir):
        os.mkdir(topdir)
    if os.path.exists(os.path.join(topdir, package)):
        tty.msg('stage: directory "{0}" exists: skipping'.format(package))
        return
    tty.msg('staging '  + package)
    spec.package.path\
        = '{0}/spackdev-aux/.tmp'.format(os.environ['SPACKDEV_BASE'])
    spec.package.do_stage()
    shutil.move('{0}/{1}'.format(spec.package.path, package),
                '{0}/'.format(topdir))

def stage_packages(packages, package_specs):
    for package in packages:
        stage_package(package, package_specs[package])


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
