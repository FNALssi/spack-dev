import os
import re

from llnl.util import tty
from six.moves import shlex_quote as cmd_quote
from six.moves import cPickle

import fnal.spack.dev as dev

_var_finder\
    = re.compile(r'^(?:export\s+)?(?P<var>[A-Za-z_][A-Za-z_0-9()]*)=(?P<val>(?P<sp>\')?.*?(?(sp)\')(?:;\s+export\s+\1;?)?$)',
                 re.DOTALL | re.MULTILINE)


# Deal with possibly quoted values, with optional leading export
# keyword or trailing statement.
def environment_from_string(env_string):
    environment=dict((match.group('var'), match.group('val')) for
                     match in _var_finder.finditer(env_string))
    return environment


def environment_from_pickle(path):
    environment = cPickle.load(open(path, 'rb'))
    assert(type(environment) == dict)
    return environment


# Variable blacklist.
_var_blacklist\
    = re.compile(r'(?:.*AUTH.*|.*SESSION.*|DISPLAY$|HOME$|KONSOLE_|PROMPT_COMMAND$|PS\d|(?:OLD)?PWD$|SHLVL$|SSH_|TERM$|USER$|WINDOWID$|XDG_|_$)')
# Variable whitelist.
_var_whitelist = re.compile(r'SPACK(?:DEV)?_')


def sanitized_environment(environment, drop_unchanged=False):
    return dict((var, val) for (var, val) in environment.iteritems()
                if _var_whitelist.match(var) or not
                (_var_blacklist.match(var) or
                 (drop_unchanged and var in os.environ and
                  val == cmd_quote(os.environ[var]))))


def bootstrap_environment(pathname=''):
    if pathname or 'SPACKDEV_BASE' not in os.environ:
        env_file_name = os.path.join(pathname, dev.spackdev_aux_subdir, 'env.pickle')
        if os.path.exists(env_file_name):
            os.environ.update(sanitized_environment
                              (environment_from_pickle(env_file_name)))
        else:
            tty.die('unable to find spackdev area{pname}: please source {env_sh} or execute from parent of {aux_subdir}'.
                    format(pname=' ({0})'.format(pathname) if pathname else '',
                           env_sh=os.path.join(dev.spackdev_aux_subdir, 'env.sh'),
                           aux_subdir=dev.spackdev_aux_subdir))


def srcs_topdir():
    bootstrap_environment()
    result = os.path.join(os.environ['SPACKDEV_BASE'], 'srcs')
    return result
