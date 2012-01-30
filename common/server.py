#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from SimpleXMLRPCServer import SimpleXMLRPCServer

#import os
import fcntl
import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
import threading

class PNCXMLRPCServer(SocketServer.ThreadingTCPServer,
                         SimpleXMLRPCDispatcher):
    allow_reuse_address = True

    _send_traceback_header = False

    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler,
                 logRequests=True, allow_none=False, encoding=None, bind_and_activate=True):
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
        SocketServer.ThreadingTCPServer.__init__(self, addr, requestHandler, bind_and_activate)

        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)

class Server(PNCXMLRPCServer):
    def __init__(self, addr):
        PNCXMLRPCServer.__init__(self, addr)
        self.__running = False

    def is_running(self):
        return self.__running
        
    def start(self):
        if self.__running is True:
            raise Exception, "Server is running."

        self.__running = True
        
#        if os.fork() == 0:
#            self.serve_forever()
        try: threading.Thread(target=self.serve_forever).start()
        except: pass

    def stop(self):
        try: self.server_close()
        except: pass
        self.__running = False
        print "Server stop..."

def main():
    pass
    
if __name__ == '__main__':
    main()