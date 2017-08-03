#!/usr/bin/env python

from spackdev.external_tools import find_library_version


class Openssl:
    def find(self):
        all_prefixes = ['/usr', '/usr/local', '/usr/local/opt/openssl']
        return find_library_version('openssl', 'openssl/opensslv.h',
                                    'OPENSSL_VERSION_TEXT',
                                    regexp='[0-9\.]+[a-z0-9-]*',
                                    prefixes=all_prefixes)
