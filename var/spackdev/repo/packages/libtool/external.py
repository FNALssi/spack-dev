#!/usr/bin/env python

from spackdev.external_tools import find_executable_version
import sys


class Libtool:
    def find(self):
        if sys.platform == 'darwin':
            retval = find_executable_version('libtool', '-V', '[a-z]+-[0-9]+')
        else:
            retval = find_executable_version('libtool')
        return retval
