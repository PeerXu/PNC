'''
Created on 2012-1-16

@author: peer
'''
import unittest
import random
import config


class Test(unittest.TestCase):
    def test_threads_service(self):
        import xmlrpclib
        import threading
        from common import data
        
        def threads_on_run_instance(rand):
            params = data.VirtualMachine()
            params.cores = 1
            params.disk = 0
            params.mem = 64
            server_url = 'http://%s:%d' % (config.NODE_ADDR[0], config.NODE_ADDR[1])
#            server = xmlrpclib.ServerProxy(server_url)
#            result = server.do_run_instance(
#                                            "test%s" % (str(rand.random())),
#                                            #"test",
#                                            "None",
#                                            params, # VirtualMachine
#                                            "None",
#                                            "/home/cloud/image/xp.qcow2",
#                                            "None",
#                                            "None",
#                                            "None",
#                                            "None",
#                                            {}, # net_config
#                                            "None")
            server = xmlrpclib.ServerProxy(server_url, allow_none=True)
            result = server.do_run_instance(
                                            "test%s" % (str(rand.random())),
                                            #"test",
                                            None,
                                            params, # VirtualMachine
                                            None,
                                            "/home/cloud/image/xp.qcow2",
                                            None,
                                            None,
                                            None,
                                            None,
                                            {}, # net_config
                                            None)
            if result["code"]:
                assert False
            Test.assertEqual(self, result["data"], 'run instance')
        
        rand = random.Random()
        thread_count = 1
        threads = []
        [threads.append(threading.Thread(target=threads_on_run_instance, args=(rand,))) for _ in xrange(thread_count)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_threads_service']
    unittest.main()