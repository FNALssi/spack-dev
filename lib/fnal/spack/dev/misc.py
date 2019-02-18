#!/usr/bin/env python

import sys
import os
import ast
import time
from llnl.util import tty
import spack.cmd
import spack.spec
if sys.version_info[0] > 2 and sys.version_info[1] > 2:
    import shutil
else:
    from distutils import spawn

def read_package_info(want_specs=True):
    packages_filename = os.path.join('spackdev-aux', 'packages.sd')
    with open(packages_filename, 'r') as f:
        first_line = f.readline().rstrip()
        if first_line.find('[') > -1:
            tty.die('packages.sd in obsolete (unsafe) format: please re-execute spack init or initialize a new spackdev area.')
        requesteds = first_line.split()
        additional = f.readline().rstrip().split()
        deps = f.readline().rstrip().split()

    install_specs = []
    if want_specs:
        specs_dir = os.path.join('spackdev-aux', 'spec')
        if not os.path.exists(specs_dir):
            tty.die('YAML spec information missing: please re-execute spack init or initialize a new spackdev area.')
        for spec_file in os.listdir(specs_dir):
            if spec_file.endswith('.yaml'):
                with open(os.path.join(specs_dir, spec_file), 'r') as f:
                    install_specs.append(spack.spec.Spec.from_yaml(f))
        return requesteds, additional, deps, install_specs

    return requesteds, additional, deps


def which(executable):
    if sys.version_info[0] > 2 and sys.version_info[1] > 2:
        return shutil.which(executable)
    else:
        return spawn.find_executable(executable)
