'''
Created on Mar 3, 2012

@author: peer
'''
import unittest

import xmlrpclib

class Test(unittest.TestCase):

    def test_add_node(self):
        cluster = xmlrpclib.ServerProxy('http://localhost:18002')
        ret = cluster.do_add_node('n1', 'localhost', 18003)
        self.assertEqual(ret['code'], 0)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_add_node']
    unittest.main()