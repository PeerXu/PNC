#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import server
from common import logger
import os
import sys

class Controller(object):
    PREFIX = 'do_'
    
    def __init__(self, addr, logname, logfile, loglevel, is_daemon=True):
        self.__server = server.Server(addr)
        self.__methods = None
        self._logger = logger.get_logger_object(name=logname, filename=logfile, level=loglevel)
        self.__is_daemon = is_daemon
        self.self_register()

    def self_register(self):
        self.__methods = [m for m in dir(self) if m.startswith(Controller.PREFIX)]
        self.__server.register_instance(self)

    def methods(self):
        return self.__methods
        
    def start(self):
        if self.__is_daemon:
            self.__daemonize()
        try: self.__server.start()
        except: pass
        
    def stop(self):
        self.__server.stop()
        
#    def info(self, msg, *args, **kwargs):
#        self.__logger.info(msg, *args, **kwargs)
#    def warning(self, msg, *args, **kwargs):
#        self.__logger.warning(msg, *args, **kwargs)
#    def error(self, msg, *args, **kwargs):
#        self.__logger.error(msg, *args, **kwargs)
#    def critical(self, msg, *args, **kwargs):
#        self.__logger.critical(msg, *args, **kwargs)
#    def debug(self, msg, *args, **kwargs):
#        self.__logger.debug(msg, *args, **kwargs)        
        
    def __daemonize(self): 
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
        os.setsid()
        os.umask(0)
        pid = os.fork()
        if pid > 0:
            sys.exit(0)