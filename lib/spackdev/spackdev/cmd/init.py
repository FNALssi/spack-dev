#!/usr/bin/env python
from __future__ import print_function

import argparse
from spackdev import spack_cmd, external_cmd
from spackdev import stage_packages, install_dependencies
from spackdev.spack_import import tty
from spackdev.spack_import import yaml
from spackdev import which

# from spackdev.spack import Spec
import copy
import glob
import os
import re
import shutil
import stat
import subprocess
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
        self.all_packages = {}

    def add(self, package, spec, dependencies):
        if not self.deps.has_key(package):
            self.deps[package] = dependencies.keys()
        else:
            append_unique(dependencies.keys(), self.deps[package])
        self.all_packages[package] = spec
        self.all_packages.update\
            ({key: val for (key, val) in dependencies.iteritems() if not
              self.all_packages.has_key(key)})

    def get_dependencies(self, package):
        if self.deps.has_key(package):
            retval = self.deps[package]
        else:
            retval = []
        return retval

    def get_all_dependencies(self, package, retval = None):
        if retval is None:
            retval = []
        for subpackage in self.get_dependencies(package):
            append_unique(subpackage, retval)
            self.get_all_dependencies(subpackage, retval)
        return retval

    def get_all_packages(self):
        return self.all_packages

    def package_info(self, package):
        # Will raise KeyError if package is not found.
        return self.all_packages[package]

    def has_dependency(self, package, other_packages):
        for other in other_packages:
            if other in self.get_dependencies(package):
                return True
        else:
            return False


class Build_system:
    def __init__(self, system_type):
        self.label = system_type
        if system_type == 'make':
            self.build_command = 'make'
            self.cmake_label = '"Unix Makefiles"'
        elif system_type == 'ninja':
            if which('ninja'):
                self.build_command = 'ninja'
            elif which('ninja-build'):
                self.build_command = 'ninja-build'
            else:
                tty.msg('warning: ninja build selected, but neither "ninja" nor "ninja-build" are available')
                self.build_command = 'ninja'
            self.cmake_label = 'Ninja'
        else:
            tty.die('Build_system: must be either "make" or "ninja"')


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


def yaml_to_specs(yaml_text):
    documents = []
    document = ''
    for line in yaml_text.split('\n'):
        if line == 'spec:':
            if len(document) > 0:
                documents.append(document)
            document = 'spec:\n'
        else:
            document += line + '\n'
    if len(document) > 0:
        documents.append(document)
    super_specs = map(yaml.load, documents)
    specs = {}
    for spec in super_specs:
        for sub_spec in spec['spec']:
            specs.update({key: value for (key, value) in sub_spec.iteritems() if key not in specs})
    return specs


def extract_specs(spec_source):
    cmd = ['spec', '--yaml']
    if type(spec_source) == list:
        # List of packages.
        cmd.extend(spec_source)
    else:
        # File containing spack install specification.
        with open(spec_source, 'r') as dag_file:
            cmd.append(dag_file.read().rstrip())
    status, output = spack_cmd(cmd)
    specs = yaml_to_specs(output)
    return specs


def calculate_dependencies(specs):
    dependencies = Dependencies()
    for name in specs.keys():
        if specs[name].has_key('dependencies'):
            spec_deps = specs[name]['dependencies']
            package_dependencies \
                = {d: spec_deps[d] for d in spec_deps.keys()}
        else:
            package_dependencies = {}
        dependencies.add(name, specs[name], package_dependencies)
    return dependencies


def get_additional(requested, dependencies):
    additional = []
    for package in requested:
        append_unique([dep for dep in
                       dependencies.get_all_dependencies(package) if
                       dep not in requested and
                       dependencies.has_dependency(dep, requested)],
                      additional)
    return additional


def init_cmakelists(project='spackdev'):
    f = open(os.path.join('spackdev', 'CMakeLists.txt'), 'w')
    f.write(
        '''cmake_minimum_required(VERSION ${{CMAKE_VERSION}})
        project({0})
        set(SPACKDEV_SOURCE_DIR "{1}")
        '''.format(project, os.getcwd()))
    return f


def add_package_to_cmakelists(cmakelists, package, dependencies, cmake_args,
                              build_system):

    cmake_wrapper = os.path.join(os.getcwd(), 'spackdev', package, 'bin',
                                 'cmake')
    cmakelists.write(
'''
# {package}
file(MAKE_DIRECTORY ${{CMAKE_BINARY_DIR}}/tags/{package})
file(MAKE_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package})

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
  COMMAND {cmake_wrapper} 
      {cmake_args}
      -G {cmake_build_label}
      -DCMAKE_INSTALL_PREFIX=${{CMAKE_BINARY_DIR}}/install
      ${{SPACKDEV_SOURCE_DIR}}/{package} && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
'''.format(package=package, cmake_wrapper=cmake_wrapper,
           cmake_args=cmake_args,
           cmake_build_label=build_system.cmake_label))

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

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/{build_label}
  COMMAND {build_command} && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/{build_label}_dummy
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/cmake
)

add_custom_target(tags_{package}_{build_label}
DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/{build_label})
add_dependencies(tags_{package}_{build_label} tags_{package}_cmake)

set_source_files_properties(
  ${{CMAKE_BINARY_DIR}}/tags/{package}/{build_label}
  PROPERTIES GENERATED TRUE
)

add_custom_command(OUTPUT ${{CMAKE_BINARY_DIR}}/tags/{package}/install
  COMMAND {build_command} install && touch ${{CMAKE_BINARY_DIR}}/tags/{package}/install_dummy
  WORKING_DIRECTORY ${{CMAKE_BINARY_DIR}}/{package}
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/{build_label}
)

add_custom_target(tags_{package}_install
  ALL
  DEPENDS ${{CMAKE_BINARY_DIR}}/tags/{package}/install)

add_dependencies(tags_{package}_install tags_{package}_{build_label})

set_source_files_properties(
  ${{CMAKE_BINARY_DIR}}/tags/{package}/install
  PROPERTIES GENERATED TRUE
)

'''.format(package=package, build_command=build_system.build_command,
           build_label=build_system.label))


def extract_cmake_args(packages, install_args):
    retval, output = spack_cmd(['install', '--fake', '--only', 'package',
                                install_args])
    package_cmake_args = {}
    for line in output.splitlines():
        if line.startswith('[cmake-args]'):
            tag, package, cmake_args = line.split(None, 2)
            package_cmake_args[package] = cmake_args
    missing_packages = []
    for package in packages:
        if package not in package_cmake_args:
            missing_packages.append(package)
    if missing_packages:
        tty.die('unable to ascertain CMake arguments for packages: {0}'.
                format(' '.join(missing_packages)))

    retval, output = spack_cmd(['uninstall', '-y', install_args])
    return package_cmake_args


def write_cmakelists(packages, install_args, dependencies, build_system):
    package_cmake_args = extract_cmake_args(packages, install_args)
    cmakelists = init_cmakelists()
    remaining_packages = copy.copy(packages)
    while remaining_packages != []:
        for package in remaining_packages:
            if not dependencies.has_dependency(package, remaining_packages):
                package_dependencies = []
                for dependency in dependencies.get_dependencies(package):
                    if dependency in packages:
                        package_dependencies.append(dependency)
                add_package_to_cmakelists(cmakelists, package,
                                          package_dependencies,
                                          package_cmake_args[package],
                                          build_system)
                remaining_packages.remove(package)


def get_environment(package):
    package_env_file_name = '{0}-environment.txt'.format(package)
    status, output \
        = spack_cmd(['env', '--dump', package, package_env_file_name])
    package_env_file = open(package_env_file_name, 'r')
    package_env = package_env_file.read()
    environment = {}
    # Deal with possibly quoted values.
    var_regex \
        = re.compile(r'^export ([A-Za-z_][A-Za-z_0-9()]*)=((?P<sp>\')?.*?(?(sp)\')$)',
                     re.DOTALL | re.MULTILINE)
    for match in var_regex.finditer(package_env):
        if not match.group(1).startswith('BASH_FUNC'):
            environment[match.group(1)] = match.group(2)
    return environment


def copy_modified_script(source, dest, environment):
    infile = open(source, 'r')
    outfile = open(dest, 'w')

    # copy hash bang line
    line = infile.readline()
    outfile.write(line)

    # insert select variables
    outfile.write('# begin SpackDev variables\n')
    for var, value in sorted(environment.iteritems()):
        if var in ['CMAKE_PREFIX_PATH', 'PATH']:
            outfile.write('{0}={1}\n'.format(var,value))
            outfile.write('export {0}\n'.format(var))
        s_spack = re.match('^SPACK_.*', var)
        if s_spack:
            if var == 'SPACK_PREFIX':
                spack_prefix = os.path.join(os.getcwd(), 'build', 'install')
                outfile.write(var + '=' + spack_prefix + '\n')
            else:
                outfile.write('{0}={1}\n'.format(var,value))
            outfile.write('export {0}\n'.format(var))
    outfile.write('# end SpackDev variables\n')

    # copy the rest
    for line in infile.readlines():
        outfile.write(line)
    outfile.close()
    os.chmod(dest, 0755)


def create_cmake_wrapper(wrappers_dir, environment, dependencies, dev_packages):
    filename = os.path.join(wrappers_dir, 'cmake')
    f = open(filename, 'w')
    f.write('# /bin/sh\n')
    f.write('\n# begin spack variables\n')
    for var, value in sorted(environment.iteritems()):
        f.write('{0}={1}\n'.format(var,value))
        f.write('export {0}\n'.format(var))
    f.write('\n# end spack variables\n')
    f.write('\n')
    for dep in dependencies:
        if dep in dev_packages:
            package_src = os.path.join(os.getcwd(), dep)
            f.write('CMAKE_PREFIX_PATH="' + package_src +
                    ':$CMAKE_PREFIX_PATH"\n')
    f.write('exec cmake "$@"\n')
    f.close()
    os.chmod(filename, 0755)


def create_wrappers(package, environment, dependencies, dev_packages):
    # print 'jfa start create_wrappers'
    wrappers_dir = os.path.join('spackdev', package, 'bin')
    # wrappers_dir = os.path.join('env', package, 'bin')
    if not os.path.exists(wrappers_dir):
        os.makedirs(wrappers_dir)
    for var, value in sorted(environment.iteritems()):
        if var in ['CC', 'CXX', 'F77', 'FC']:
            if value[0] == "'" and value[-1] == "'":
                # It's been quoted: we need the shell to unquote it.
                value=subprocess.call("echo {0}".format(value), shell=True)
            filename = os.path.basename(value)
            dest = os.path.join(wrappers_dir, filename)
            environment[var] = os.path.join(os.getcwd(), dest)
            copy_modified_script(value, dest, environment)
    create_cmake_wrapper(wrappers_dir, environment, dependencies, dev_packages)


def create_env_sh(package, environment):
    env_dir = os.path.join('spackdev', package, 'env')
    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    pathname = os.path.join(env_dir, 'env.sh')
    # pathname = os.path.join('env', package, 'env.sh')
    outfile = open(pathname, 'w')
    for var, value in sorted(environment.iteritems()):
        outfile.write('{0}={1}\n'.format(var, value))


def create_stage_script(package):
    bin_dir = os.path.join('spackdev', package, 'bin')
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    status, output = spack_cmd(["exportstage", package])
    output_lines = output.split('\n')
    # print 'jfa: output_lines =',output_lines
    # print 'jfa: output_lines[1] =', output_lines[1]
    method = output_lines[0]
    dict_str = output_lines[1]
    stage_py_filename = os.path.join(bin_dir, 'stage.py')
    stage_py = open(stage_py_filename, 'w')
    stage_py.write('''#!/usr/bin/env python
import os
import subprocess
import sys
def stage(package, method, the_dict):
    if method == 'GitFetchStrategy':
        cmd = ['git', 'clone']
        if the_dict['branch']:
            cmd.extend(['--branch', the_dict['branch']])
        cmd.extend([the_dict['url'], package])
        retval = subprocess.call(cmd)
        if retval != 0:
            sys.stderr.write('"' + ' '.join(cmd) + '" failed\\n')
            sys.exit(retval)
        os.chdir(package)
        if the_dict['tag']:
            retval = subprocess.call(['git', 'checkout', the_dict['tag']])
            if retval != 0:
                sys.stderr.write('"' + ' '.join(cmd) + '" failed\\n')
                sys.exit(retval)
    else:
        sys.stderr.write('SpackDev stage.py does not yet handle sources of type ' + method)
        sys.exit(1)
    ''')
    stage_py.write('''
if __name__ == '__main__':
    package = "''')
    stage_py.write(package)
    stage_py.write('''"
    method = "''')
    stage_py.write(output_lines[0])
    stage_py.write('''"
    the_dict = ''')
    stage_py.write(dict_str)
    stage_py.write('''
    stage(package, method, the_dict)
    ''')
    stage_py.close()
    os.chmod(stage_py_filename, 0755)


def create_environment(packages, all_dependencies):
    pkg_environments = {}
    for package in packages:
        environment = get_environment(package)
        pkg_environments[package] = environment
        # print package,':'
        # for line in environment:
        #     print line
        create_wrappers(package, environment,
                        all_dependencies.get_dependencies(package),
                        packages)
        create_env_sh(package, environment)
        create_stage_script(package)
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
        status, output = spack_cmd(["diy", "--dry-run-file", "spackdev.out",
                                          short_spec])
        os.chdir("..")
        extract_build_step_scripts(package, os.path.join(package, "spackdev.out"))


def par_val_to_string(par, val):
    if type(val) == list:
        retval = ' {0}={1}'.format(par, ' '.join(val)) if val else ''
    elif type(val) == tuple:
        retval = ' {0}={1}'.format(par, ' '.join(val)) if val else ''
    elif type(val) == bool:
        retval = '+{0}'.format(par) if val else '~{0}'.format(par)
    elif type(val) == None:
        retval = ''
    else:
        retval = ' {0}={1}'.format(par, val)
    return retval


def install_args_for_package(package, all_dependencies):
    package_info = all_dependencies.package_info(package)
    version = '@{0}'.format(package_info['version'])
    compiler = '%{0}@{1}'.format(package_info['compiler']['name'],
                                 package_info['compiler']['version']) \
        if package_info.has_key('compiler') else ''

    pars = package_info['parameters']
    bool_args = []
    other_args = []
    for (par, val) in pars.iteritems():
        parstring = par_val_to_string(par, val)
        if parstring:
            alist = bool_args if parstring.startswith(('+', '~')) else \
                    other_args
            alist.append(parstring)
    return [package, version, compiler] + bool_args + other_args


def format_packages_for_install(packages, all_dependencies):
    install_args = []
    for package in packages:
        install_args.append\
            (''.join(install_args_for_package(package, all_dependencies)))
        install_args.extend\
            (["^{0}".format\
              (''.join(install_args_for_package(dep,
                                                all_dependencies)))
              for dep in all_dependencies.get_all_dependencies(package)])
    return ' '.join(install_args)


def write_packages_file(requested, additional, all_dependencies):
    packages_filename = os.path.join('spackdev', 'packages.sd')
    install_args = ''
    with open(packages_filename, 'w') as f:
        f.write(' '.join(requested) + '\n')
        f.write(' '.join(additional) + '\n')
        install_args = format_packages_for_install(requested + additional,
                                                   all_dependencies)
        f.write(install_args + '\n')
    return install_args

def create_build_area(build_system):
    os.mkdir('build')
    os.chdir('build')
    external_cmd(['cmake', '../spackdev',
                  '-G {}'.format(build_system.cmake_label)])


def setup_parser(subparser):
    subparser.add_argument('packages', nargs=argparse.REMAINDER,
                           help="specs of packages to add to SpackDev area")
    subparser.add_argument('--dag-file',
                           help='packages and dependencies should be inferred from the DAG specified in this text file (in "spack install" format)')
    subparser.add_argument('-d', '--no-dependencies', action='store_true', dest='no_dependencies',
                           help="do not have spack install dependent packages")
    subparser.add_argument('-m', '--make', action='store_true', dest='make',
        help="use make instead of ninja")
    subparser.add_argument('-s', '--no-stage', action='store_true', dest='no_stage',
        help="do not stage packages")


def init(parser, args):
    dir = os.getcwd()
    if (not os.path.exists(dir)):
        os.makedirs(dir)
    os.chdir(dir)
    if (os.path.exists('spackdev')) :
        tty.die('spackdev init: cannot re-init (spackdev directory exists)')
    os.mkdir('spackdev')

    requested = args.packages
    dag_filename = args.dag_file
    tty.msg('requested packages: {0}{1}'.\
            format(', '.join(requested),
                   ' from DAG as specified in {0}'.format(dag_filename)
                   if dag_filename else ''))
    specs = extract_specs(dag_filename if dag_filename else requested)
    all_dependencies = calculate_dependencies(specs)
    additional = get_additional(requested, all_dependencies)
    if additional:
        tty.msg('additional inter-dependent packages: ' +
                ' '.join(additional))
    dev_packages = requested + additional
    install_args = write_packages_file(requested, additional, all_dependencies)

    if not args.no_dependencies:
        tty.msg('install dependencies')
        (retval, output) = install_dependencies(dev_packages=dev_packages,
                                                install_args=install_args)

    if args.make:
        build_system = Build_system('make')
    else:
        build_system = Build_system('ninja')

    tty.msg('generate top level CMakeLists.txt')
    write_cmakelists(dev_packages, install_args,
                     all_dependencies, build_system)

    tty.msg('creating wrapper scripts')
    pkg_environments = create_environment(dev_packages, all_dependencies)

    if not args.no_stage:
        tty.msg('staging sources for {0}'.format(dev_packages))
        stage_packages(dev_packages)

    #create_build_scripts(dev_packages, pkg_environments)
    tty.msg('creating build area')
    create_build_area(build_system)
