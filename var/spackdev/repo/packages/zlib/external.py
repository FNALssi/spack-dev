#!/usr/bin/env python

from spackdev.external_tools import find_library_version


class Zlib:
    def find(self):
        return find_library_version('zlib', 'zlib.h', 'ZLIB_VERSION')
