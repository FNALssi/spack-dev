#!/usr/bin/env python

from spackdev.external_tools import find_executable_version


class Lua:
    def find(self):
        return find_executable_version('lua', '-v')
