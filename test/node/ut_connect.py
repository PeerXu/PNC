#!/usr/bin/env python

import unittest
import xmlrpclib
import config

class Test(unittest.TestCase):
    def test_connect(self):
        server_url = 'http://%s:%d' % (config.NODE_ADDR[0], config.NODE_ADDR[1])
        server = xmlrpclib.ServerProxy(server_url, allow_none=True)
        result = server.do_get_version()
        self.assertEqual(result, config.VERSION)

if __name__ == '__main__':
    unittest.main()
