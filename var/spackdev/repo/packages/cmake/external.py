#!/usr/bin/env python

from spackdev import external_tools, External_package


class Cmake:
    def doit(self):
        print('Cmake.doit: doing it\n')

    def find(self):
        pathname = external_tools.which_in_path('cmake')
        print('jfa: found cmake in ', pathname)
        version = external_tools.extract_version(pathname)
        print('jfa: found cmake version ', version)
        return External_package('cmake', version, pathname)
