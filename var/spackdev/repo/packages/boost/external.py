#!/usr/bin/env python

from spackdev.external_tools import find_library_version


class Boost:
    def find(self):
        external_package = find_library_version('boost', 'boost/version.hpp',
                                   'BOOST_LIB_VERSION')
        external_package.version = external_package.version.replace('_','.')
        return external_package
