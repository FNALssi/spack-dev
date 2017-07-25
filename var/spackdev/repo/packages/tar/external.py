#!/usr/bin/env python

from spackdev import external_tools


class Tar:
    def doit(self):
        print('Tar.doit: doing it\n')

    def find(self):
        pathname = external_tools.which_in_path('tar')
        print('jfa: found tar in ', pathname)
