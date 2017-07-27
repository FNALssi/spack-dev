#!/usr/bin/env python

from spackdev.external_tools import find_executable_version


class Curl:
    def find(self):
        return find_executable_version('curl')

