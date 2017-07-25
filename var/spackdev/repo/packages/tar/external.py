#!/usr/bin/env python

from spackdev import external_tools


class Tar:
    def doit(self):
        print('Tar.doit: doing it\n')
        # print('dir(spackdev) =', dir(spackdev))

    def find(self):
        print('jfa wtf:', dir(external_tools))
        pathname = external_tools.which_in_path('tar')
        print('jfa: found tar in ', pathname)
        #       exe = external_tools.which_in_path('tar')
