'''
Created on Mar 4, 2012

@author: peer
'''
import unittest
import xmlrpclib

from common import data

class Test(unittest.TestCase):


    def test_on_run_instances(self):
        params = data.VirtualMachine()
        params.cores = 1
        params.disk = 0
        params.mem = 1024
        server = xmlrpclib.ServerProxy('http://localhost:18002', allow_none=True)
        result = server.do_run_instances(["inst-1-arch"],
                                        None,
                                        None,
                                        params,
                                        None, '/opt/PNC/images/1.img',
                                        None, None,
                                        None, None,
                                        ['aa:aa:aa:aa:aa:aa'],
                                        None)
        self.assertEqual(result['code'], 0)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_on_run_instances']
    unittest.main()