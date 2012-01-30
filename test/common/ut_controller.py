#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import xmlrpclib

MAX_THREAD = 1000
URI = 'http://localhost:8080'

def thread_test_controller(fn, *args, **kwargs):
    threads = []
    [threads.append(threading.Thread(target=fn, args=args, kwargs=kwargs)) for _ in xrange(MAX_THREAD)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    server = xmlrpclib.ServerProxy(URI)
    try: server.stop()
    except: pass
    
def thread_test_on_gen(s, n):
    name = threading.current_thread().getName()
    check_str = s * n
    server = xmlrpclib.ServerProxy(URI)
    methods = server.methods()
    if 'on_gen' not in methods:
        assert False, 'method not found'
        return 1
    ret = server.on_gen(s, n)    
    assert ret == check_str, 'result error'
    print 'Pass:', name
    
def main():
    #thread_test_controller(thread_test_on_gen, 'a', 1000)
    import commands
    (_status, output) = commands.getstatusoutput("pwd")
    print output
    
if '__main__' == __name__:
    main()