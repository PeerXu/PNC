#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import threading

from common import server
from common import logger

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

    def _startup_monitor_thread(self, *args, **kwargs):
        self._logger.debug("invoked.")
        self._monitor_thread = threading.Thread(target=self._thread_monitor, args=())
        self._monitor_thread.setDaemon(True)
        self._monitor_thread.start()

    def _thread_monitor(self):
        """
        Overwrite me
        """
        
    def __daemonize(self): 
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
        os.setsid()
        os.umask(0)
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
