#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import threading

import config
from common.controller import Controller
from common import utils
from common.data import ClusterDetail

class Cluster(Controller):
    ADDR = config.CLUSTER_ADDR
    def __init__(self, is_daemon=True):
        Controller.__init__(self, Cluster.ADDR, "cluster", config.CLUSTER_LOG, config.LOG_LEVEL, is_daemon)
        self._logger.info("initialze controller done")
        
        self._initialized = 0
        self._cc_detail = ClusterDetail()

        self._inst_lock = None
        self._res_lock = None
        self._nccall_sem = None

    def _init_cluster(self):
        pass

    def start(self):
        self._logger.info("initialize cluster detail")
        
        rs = self._init_cluster()
        if rs == 1:
            self._logger.error("cluster has _initialized")
            sys.exit(1)
        elif rs == -1:
            self._logger.critical("startup cluster failed")
            sys.exit(1)
        self._logger.debug("initialize cluster detail done")

        #startup service
        self._logger.info("startup service")
        super(Cluster, self).start()
        self._logger.debug("start service done")

    def stop(self):
        self._logger.info("invoked")
        super(Cluster, self).stop()
        self._logger.debug("done")
        return Result.new(0x0, "stop service")
