#!/usr/bin/env python

import os
import sys
from commands import getstatusoutput

status, spack_root = getstatusoutput('spack location --spack-root')
if status != 0:
    sys.stderr.write('SpackDev: failed to get location of spack installation')
    sys.exit(1)

if sys.version_info[0] == 2:
    lib_dir = 'lib'
else:
    lib_dir = 'lib3'
sys.path.append(os.path.join(spack_root, 'lib', 'spack', 'external', 'yaml', lib_dir))
sys.path.append(os.path.join(spack_root, 'lib', 'spack'))
from spack.util.environment import dump_environment, pickle_environment, env_var_to_source_line
import yaml
import llnl.util.tty as tty


tty.set_verbose(True)
# import spack.spack
# print 'jfa dir(spack.spack): ', dir(spack.spack)
