#!/usr/bin/env python

import argparse
from spackdev import utils
import re
import glob
import os
import copy
import shutil
import sys

description = "initialize a spackdev area"


def append_unique(item, the_list):
    if type(item) == list:
        for subitem in item:
            append_unique(subitem, the_list)
    elif (not item in the_list) and (not item == []):
        the_list.append(item)


class Dependencies:
    def __init__(self):
        self.deps = {}
        self.all_packages = []

    def add(self, package, dependency):
        if not self.deps.has_key(package):
            self.deps[package] = []
            self._append_unique(dependency, self.all_packages)
        if dependency and (not dependency in self.deps[package]):
            self.deps[package].append(dependency)
            self._append_unique(dependency, self.all_packages)

    def get_dependencies(self, package):
        if self.deps.has_key(package):
            retval = self.deps[package]
        else:
            retval = []
        return retval

    def _append_unique(self, item, the_list):
        if type(item) == list:
            for subitem in item:
                # print 'wtf calling with', subitem
                self._append_unique(subitem, the_list)
        elif (not item in the_list) and (not item == []):
            the_list.append(item)

    def get_all_dependencies(self, package, retval = []):
        for subpackage in self.get_dependencies(package):
            self._append_unique(subpackage, retval)
            for subsubpackage in self.get_dependencies(subpackage):
                self._append_unique(self.get_dependencies(subsubpackage), retval)
        return retval

    def get_all_packages(self):
        return self.all_packages

    def has_dependency(self, package, other_packages):
        retval = False
        for other in other_packages:
            if other in self.get_dependencies(package):
                retval = True
        return retval


def extract_stage_dir_from_output(output, package):
    stage_dir = None
    for line in output.split('\n'):
        s = re.search('.*stage.*in (.*)', line)
        if s:
            stage_dir = s.group(1)
    if stage_dir:
        real_dir = glob.glob(os.path.join(stage_dir, '*'))[0]
        parent = os.path.dirname(stage_dir)
        os.rename(real_dir, os.path.join(parent, package))
        shutil.rmtree(stage_dir)
    else:
        raise RuntimeError("extract_stage_dir_from_output: failed to find stage_dir")

def stage(packages):
    for package in packages:
        status, output = utils.spack_cmd(["stage", "--path", ".", package])
        extract_stage_dir_from_output(output, package)

def add_package_dependencies(package, dependencies):
    status, output = utils.spack_cmd(["graph", "--dot", package])
    for line in output.split('\n'):
        s = re.search(' *"(.*)" -> "(.*)"', line)
        if s:
            # print 'depends', s.group(1), s.group(2)
            dependencies.add(s.group(1), s.group(2))

def get_all_dependencies(packages):
    dependencies = Dependencies()
    for package in packages:
        add_package_dependencies(package, dependencies)
    return dependencies

def get_additional(requesteds, dependencies):
    additional = []
    for package in dependencies.get_all_packages():
        package_dependencies = dependencies.get_dependencies(package)
        for requested in requesteds:
            if requested in package_dependencies:
                append_unique(package, additional)
    return additional

def init_cmakelists(project='spackdev'):
    f = open('CMakeLists.txt', 'w')
    f.write(
'''cmake_minimum_required(VERSION 2.8.8)
project({})
'''.format(project))
    return f

def add_package_to_cmakelists(cmakelists, package, dependencies):

    cmakelists.write(
'''
# {package}
file(MAKE_DIRECTORY ${{CMAKE_BINARY_DIR}}/tags/{package})
file(MAKE_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package})

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
  COMMAND cmake
      -G Ninja
      -DCMAKE_INSTALL_PREFIX=${{CMAKE_BINARY_DIR}}/install
      ${{CMAKE_SOURCE_DIR}}/{package} && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
'''.format(package=package))

    for dependency in dependencies:
        cmakelists.write("  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{dependency}/install\n".
                         format(dependency=dependency))

    cmakelists.write(
''')

add_custom_target(tags_{package}_cmake
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake)

set_source_files_properties(
  ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
  PROPERTIES GENERATED TRUE
)

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/ninja
  COMMAND ninja && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/ninja_dummy
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
)

add_custom_target(tags_{package}_ninja
DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/ninja)
add_dependencies(tags_{package}_ninja tags_{package}_cmake)

set_source_files_properties(
  ${{CMAKE_BINARY_DIR}}/tags/{package}/ninja
  PROPERTIES GENERATED TRUE
)

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/install
  COMMAND ninja install && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/install_dummy
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/ninja
)

add_custom_target(tags_{package}_install
  ALL
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/install)

add_dependencies(tags_{package}_install tags_{package}_ninja)

set_source_files_properties(
  ${{CMAKE_BINARY_DIR}}/tags/{package}/install
  PROPERTIES GENERATED TRUE
)

'''.format(package=package))

def write_cmakelists(packages, dependencies):
    cmakelists = init_cmakelists()
    remaining_packages = copy.copy(packages)
    while remaining_packages != []:
        for package in remaining_packages:
            if not dependencies.has_dependency(package, remaining_packages):
                package_dependencies = []
                for dependency in dependencies.get_dependencies(package):
                    if dependency in packages:
                        package_dependencies.append(dependency)
                add_package_to_cmakelists(cmakelists, package, package_dependencies)
                remaining_packages.remove(package)

def get_environment(package):
    environment = []
    status, output = utils.spack_cmd(["env", package])
    variables = ['CC', 'CXX', 'F77', 'FC', 'CMAKE_PREFIX_PATH', 'PATH']
    for line in output.split('\n'):
        for variable in variables:
            s_var = re.match('^{}=.*'.format(variable), line)
            if s_var:
                environment.append(line)
        s_spack = re.match('^SPACK_.*=.*', line)
        if s_spack:
            environment.append(line)
    environment.sort()
    return environment

def copy_modified_script(source, dest, environment):
    infile = open(source, 'r')
    outfile = open(dest, 'w')

    # copy hash bang line
    line = infile.readline()
    outfile.write(line)

    # insert select variables
    outfile.write('# begin SpackDev variables\n')
    for pair in environment:
        s = re.match('([a-zA-Z0-9_]*)=(.*)', pair)
        if s:
            var = s.group(1)
            value = s.group(2)
            if var in ['CMAKE_PREFIX_PATH', 'PATH']:
                outfile.write(pair + '\n')
                outfile.write('export ' + var + '\n')
            s_spack = re.match('^SPACK_.*', var)
            if s_spack:
                outfile.write(pair + '\n')
                outfile.write('export ' + var + '\n')
        # else:
        #     print "jfa: failed (again?) to parse environment line:"
        #     print pair
    outfile.write('# end SpackDev variables\n')

    # copy the rest
    for line in infile.readlines():
        outfile.write(line)
    outfile.close()
    os.chmod(dest, 0755)


def create_wrappers(package, environment):
    # print 'jfa start create_wrappers'
    wrappers_dir = os.path.join('spackdev', package, 'bin')
    # wrappers_dir = os.path.join('env', package, 'bin')
    if not os.path.exists(wrappers_dir):
        os.makedirs(wrappers_dir)
    for index in range(0, len(environment)):
        s = re.match('([a-zA-Z0-9_]*)=(.*)', environment[index])
        if s:
            var = s.group(1)
            value = s.group(2)
            if var in ['CC', 'CXX', 'F77', 'FC']:
                filename = os.path.basename(value)
                dest = os.path.join(wrappers_dir, filename)
                copy_modified_script(value, dest, environment)
        # else:
        #     print 'jfa: failed to parse environment line:'
        #     print environment[index]
    # print 'jfa end create wrappers'

def create_env_sh(package, environment):
    env_dir = os.path.join('spackdev', package, 'env')
    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    pathname = os.path.join(env_dir, 'env.sh')
    # pathname = os.path.join('env', package, 'env.sh')
    outfile = open(pathname, 'w')
    for line in environment:
        outfile.write(line + '\n')

def create_environment(packages):
    pkg_environments = {}
    for package in packages:
        environment = get_environment(package)
        pkg_environments[package] = environment
        # print package,':'
        # for line in environment:
        #     print line
        create_wrappers(package, environment)
        create_env_sh(package, environment)
    return pkg_environments

def extract_build_step_scripts(package, dry_run_filename):
    # f = open(dry_run_filename, 'r')
    # lines = f.readlines()
    # f.close()
    steps = utils.read_all_csv_lists(dry_run_filename)
    # print 'jfa: found', len(steps),'build steps'
    wrappers_dir = os.path.join('spackdev', package, 'bin')
    # wrappers_dir = os.path.join('env', package, 'bin')

def extract_short_spec(package, pkg_environements):
    retval = None
    for line in pkg_environements[package]:
        s = re.match('^SPACK_SHORT_SPEC=(.*)', line)
        if s:
            rhs = s.group(1)
            s2 = re.match('(.*)=', rhs)
            retval = s2.group(1)
    return retval

def create_build_scripts(packages, pkg_environments):
    for package in packages:
        os.chdir(package)
        short_spec = extract_short_spec(package, pkg_environments)
        status, output = utils.spack_cmd(["diy", "--dry-run-file", "spackdev.out",
                                          short_spec])
        os.chdir("..")
        extract_build_step_scripts(package, os.path.join(package, "spackdev.out"))

def write_packages_file(requesteds, additional):
    packages_filename = os.path.join('spackdev', 'packages.sd')
    with open(packages_filename, 'w') as f:
        f.write(str(requesteds) + '\n')
        f.write(str(additional) + '\n')

def setup_parser(subparser):
    subparser.add_argument('packages', nargs=argparse.REMAINDER,
                           help="specs of packages to add to SpackDev area")
    subparser.add_argument('-s', '--no-stage', action='store_true', dest='no_stage',
        help="do not stage packages")


def init(parser, args):
    dir = os.getcwd()
    if (not os.path.exists(dir)):
        os.makedirs(dir)
    os.chdir(dir)
    if (os.path.exists('spackdev')) :
        sys.stderr.write('spackdev init: cannot re-init (spackdev directory exists)\n')
        sys.exit(1)
    os.mkdir('spackdev')

    requesteds = args.packages
    all_dependencies = get_all_dependencies(requesteds)
    additional = get_additional(requesteds, all_dependencies)
    write_packages_file(requesteds, additional)
    all_packages = requesteds + additional

    write_cmakelists(all_packages, all_dependencies)

    pkg_environments = create_environment(all_packages)

    if not args.no_stage:
        stage(all_packages)

    #create_build_scripts(all_packages, pkg_environments)
