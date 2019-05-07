import os
import shutil

from llnl.util import tty
from llnl.util.filesystem import mkdirp

import fnal.spack.dev as dev

import spack.spec

def read_package_info(want_specs=True):
    dev.environment.bootstrap_environment()
    packages_filename = os.path.join(os.environ['SPACKDEV_BASE'],
                                     dev.spackdev_aux_packages_subdir,
                                     'packages.sd')
    with open(packages_filename, 'r') as f:
        first_line = f.readline().rstrip()
        if first_line.find('[') > -1:
            tty.die('packages.sd in obsolete (unsafe) format: please re-execute spack init or initialize a new spackdev area.')
        requesteds = first_line.split()
        additional = f.readline().rstrip().split()
        deps = f.readline().rstrip().split()

    install_specs = []
    if want_specs:
        specs_dir = os.path.join(os.environ['SPACKDEV_BASE'],
                                 dev.spackdev_aux_specs_subdir)
        if not os.path.exists(specs_dir):
            tty.die('YAML spec information missing: please re-execute spack init or initialize a new spackdev area.')
        for spec_file in os.listdir(specs_dir):
            if spec_file.endswith('.yaml'):
                with open(os.path.join(specs_dir, spec_file), 'r') as f:
                    install_specs.append(spack.spec.Spec.from_yaml(f))
        return requesteds, additional, deps, install_specs

    return requesteds, additional, deps


def stage_package(package, spec):
    topdir = dev.environment.srcs_topdir()
    if not os.path.exists(topdir):
        os.mkdir(topdir)
    package_dest = os.path.join(topdir, package)
    if os.path.exists(package_dest):
        tty.msg('Package {0} is already staged for development: skipping'.
                format(package))
        return
    tty.msg('Staging {0} for development'.format(package))
    spec.package.path\
        = os.path.join(os.environ['SPACKDEV_BASE'],
                       dev.spackdev_aux_tmp_subdir)
    spec.package.do_stage()
    files_or_dirs\
        = ['spack-expanded-archive'] if \
        os.path.exists(os.path.join(spec.package.path,
                                    'spack-expanded-archive')) else \
        os.listdir(spec.package.path)
    if len(files_or_dirs) > 1:  # Automatic consolidation.
        mkdirp(package_dest)
    for file_or_dir in files_or_dirs:
        tty.debug('Moving {0} to {1}'.format(os.path.join(spec.package.path, file_or_dir),
                                           package_dest))
        shutil.move(os.path.join(spec.package.path, file_or_dir),
                    package_dest)


def stage_packages(packages, package_specs):
    for package in packages:
        stage_package(package, package_specs[package])


def get_package_spec(package, specs):
    return reduce(lambda a, b : a if package in a else b, specs, {})[package]


def install_dependencies(**kwargs):
    if 'dep_specs' in kwargs:
        dev_packages = kwargs['dev_packages']
        dep_specs = kwargs['dep_specs']
    else:
        # Concretization is necessary.
        (requested, additional, deps, install_specs) = read_package_info()
        dev_packages = requested + additional
        dep_specs = [ get_package_spec(dep, install_specs) for dep in deps ]

    tty.msg('requesting spack install of dependencies for: {0}'
            .format(' '.join(dev_packages)))
    for dep in dep_specs:
        tty.debug('installing dependency {0}'.format(dep.name))
        dep.package.do_install()
