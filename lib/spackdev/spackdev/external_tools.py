#!/usr/bin/env python

import commands
import os
import re
import distutils.spawn

def which_in_path(executable):
    return distutils.spawn.find_executable(executable)

def extract_version(pathname, arg='--version', regexp='[0-9\.]+'):
    command = "{0} {1}".format(pathname, arg)
    (status, output) = commands.getstatusoutput(command)
    match = re.search(regexp, output)
    return match.group(0)

def status_write(message):
    print(message)

def version_acceptable(the_str, min_version_list):
    status_write(
        "debug_config: working on found version str '%s'" % the_str
        + "\n")
    version_num_match = re.search('[0-9.]+', the_str)
    if version_num_match:
        version_num_str = version_num_match.group(0)
        garbled_str = False
        try:
            version_num_list = map(int, version_num_str.split('.'))
        except:
            garbled_str = True
            found_good_version = False
        if not garbled_str:
            status_write(
                "debug_config: comparing found version " + str(
                    version_num_list) +
                " with minimum version " + str(min_version_list)
                + "\n")
            for i in range(0, len(min_version_list)):
                if len(version_num_list) < i + 1:
                    version_num_list.append(0)
                if version_num_list[i] > min_version_list[i]:
                    found_good_version = True
                    break
                elif version_num_list[i] < min_version_list[i]:
                    found_good_version = False
                    break
                elif version_num_list[i] == min_version_list[i]:
                    found_good_version = True
    else:
        found_good_version = False
    status_write(
        "debug_config: found_good_version = " + str(found_good_version)
        + "\n")
    return found_good_version


def need_internal_executable(executable):
    cmd = 'type %s' % executable
    status_write(
        "debug_config: running command " + cmd + "\n")
    (status, output) = commands.getstatusoutput(cmd)
    status_write(
        "debug_config: execution completed with status " + str(status) +
        " and output:\n" +
        output
        + "\n")
    if status:
        retval = 1
    else:
        retval = 0
    return retval


def need_internal_version_executable(command, min_version_list, regexp=None):
    status_write(
        "debug_config: running command " + command
        + "\n")
    (status, output) = commands.getstatusoutput(command)
    status_write(
        "debug_config: execution completed with status " + str(status) +
        " and output:\n"
        + output
        + "\n")
    if status:
        found_good_version = False
    else:
        if regexp:
            match = re.search(regexp, output)
            if match:
                output = match.group(0)
            else:
                output = ''
        found_good_version = version_acceptable(output, min_version_list)
    if found_good_version:
        retval = 0
    else:
        retval = 1
    return retval


def need_internal_version_library(headers, body="",
                                  include_flags="", link_flags="",
                                  compiler="g++"):
    status_write(
        "debug_config: test compiling C++ program:\n"
        + "----------------begin----------------"
        + "\n")
    olddir = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)
    headers_list = listify(headers)
    f = open("tmp.cc", "w")
    for header in headers_list:
        f.write('#include "%s"\n' % header)
    f.write('int main()\n{\n%s\n return 0;\n}\n' % body)
    f.close()
    f = open("tmp.cc", "r")
    map(status_write, f.readlines())
    f.close()
    status_write(
        "-----------------end-----------------"
        + "\n")
    command = compiler + ' %s tmp.cc -o a.out %s' % (include_flags, link_flags)
    status_write(
        "debug_config: " + command
        + "\n")
    (status, output) = commands.getstatusoutput(command)
    status_write(
        "debug_config: compilation completed with status " + str(status)
        + " and output:\n"
        + output
        + "\n")
    retval = 0
    if status:
        retval = 1
    else:
        status_write(
            "debug_config: executing ./a.out:"
            + "\n")
        (status, output) = commands.getstatusoutput('./a.out')
        status_write(
            "debug_config: execution completed with status " + str(status)
            + " and output: "
            + output
            + "\n")
        if status:
            retval = 1
    os.chdir(olddir)
    (status, output) = commands.getstatusoutput('/bin/rm -r %s' % tmpdir)
    return retval


def need_internal_version_python_module(module, min_version_list):
    cmd = 'python -c "import %s; print %s.__version__"' % (module, module)
    status_write(
        "debug_config: running command " + cmd
        + "\n")
    (status, output) = commands.getstatusoutput(cmd)
    status_write(
        "debug_config: command completed with status " + str(status)
        + " and output:\n"
        + output
        + "\n")
    if status:
        found_good_version = False
    else:
        found_good_version = version_acceptable(output, min_version_list)
    if found_good_version:
        retval = 0
    else:
        retval = 1
    return retval
