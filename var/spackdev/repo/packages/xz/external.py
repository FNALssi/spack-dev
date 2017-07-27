#!/usr/bin/env python

from spackdev.external_tools import find_executable_version


class Xz:
    def find(self):
        return find_executable_version('xz')

