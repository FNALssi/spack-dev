#!/usr/bin/env python

import os
import sys
from commands import getstatusoutput

status, spack_root = getstatusoutput('spack location --spack-root')
if status != 0:
    sys.stderr.write('SpackDev: failed to get location of spack installation')
    sys.exit(1)

sys.path.append(os.path.join(spack_root, 'lib', 'spack'))
import external.yaml as yaml
import llnl.util.tty as tty

tty.set_verbose(True)
# import spack.spack
# print 'jfa dir(spack.spack): ', dir(spack.spack)