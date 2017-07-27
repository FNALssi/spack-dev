#!/usr/bin/env python

from spackdev import external_tools, External_package


class Tar:
    def doit(self):
        print('Tar.doit: doing it\n')

    def find(self):
        pathname = external_tools.which_in_path('tar')
        print('jfa: found tar in ', pathname)
        return External_package('tar', '1.0', pathname)

