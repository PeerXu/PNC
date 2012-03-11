'''
Created on Mar 4, 2012

@author: peer
'''

import os
import unittest
import xmlrpclib

from common import data

class ClusterTestCase(unittest.TestCase):
    
    uri = 'http://localhost:18002'
    node_id = "n1"
    inst_id = "inst-1-arch"
    img_path = '/opt/PNC/images/1.img'
    inst_mac_addr = '0b:ee:89:b0:7a:24'

    testcase_list = ('test_on_add_node',
                     'test_on_run_instances',
                     'test_on_terminate_instances')
    
    def setUp(self):
        self.cluster = xmlrpclib.ServerProxy(self.uri, allow_none=True)

    def test_on_add_node(self):
        cluster = self.cluster
        ret = cluster.do_add_node(self.node_id, 'localhost', 18003)
        self.assertEqual(ret['code'], 0)

    def test_on_run_instances(self):
        params = data.VirtualMachine()
        params.cores = 1
        params.disk = 0
        params.mem = 1024
        server = self.cluster
        result = server.do_run_instances([self.inst_id],
                                        None,
                                        None,
                                        params,
                                        None, self.img_path,
                                        None, None,
                                        None, None,
                                        [self.inst_mac_addr],
                                        None)
        self.assertEqual(result['code'], 0)
        
    def test_on_terminate_instances(self):
        cluster = self.cluster
        result = cluster.do_terminate_instances([self.inst_id])
        self.assertEqual(result['code'], 0)
    
    def tearDown(self):
        self.cluster = None
    
def suite():
    #return unittest.makeSuite(ClusterTestCase, "test")
    suite = unittest.TestSuite()
    map(lambda x: suite.addTest(ClusterTestCase(x)), ClusterTestCase.testcase_list)
    return suite
        
if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
