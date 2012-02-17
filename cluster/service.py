#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import threading

import config
from common.controller import Controller
from common import utils
from common.data import ClusterDetail, ClusterResource, ClusterInstance


class Cluster(Controller):
    ADDR = config.CLUSTER_ADDR
    def __init__(self, is_daemon=True):
        Controller.__init__(self, Cluster.ADDR, "cluster", config.CLUSTER_LOG, config.LOG_LEVEL, is_daemon)
        self._logger.info("initialze controller done")
        
        self._initialized = 0

        self._cc_detail = None

        self._inst_lock = None
        self._res_lock = None
        self._nccall_sem = None

    def _init_cluster(self):
        if self._initialized > 0:
            return 0
        elif self._initialized < 0:
            return -1
        
        # startup to initialize
        self._initialized = -1

        self._cc_resources = [] # data.ClusterResource
        self._cc_instances = [] # data.ClusterInstance
        self._cc_detail = ClusterDetail()
        
        self._inst_lock = utils.Lock()
        self._res_lock = utils.Lock()
        self._nccall_sem = utils.Semaphore(config.NC_CALL_MAX)

        # startup monitor thread
        self._startup_monitor_thread()

        # _init_cluster done. set self._initialized to 1
        self._initialized = 1

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

    def _thread_monitor(self):
        self._logger.debug("invoked.")
        while True:
            self._logger.debug("wake up")
            self._logger.debug("sleep")
            time.sleep(config.CLUSTER_MONITOR_INTERVAL)

    def do_add_node(self):
        return Result.new(0x0, "add node")

    def do_remove_node(self):
        return Result.new(0x0, "remove node")

    def do_power_down(self):
        return Result.new(0x0, "power down")

    def do_terminate_instances(self):
        return Result.new(0x0, "terminate instances")

    def do_describe_instances(self):
        return Result.new(0x0, "describe instances")

    def do_run_instances(self):
        return Result.new(0x0, "run instances")

    def do_reboot_instances(self):
        return Result.new(0x0, "reboot instances")

    def do_get_console_output(self):
        return Result.new(0x0, "console output")

    def do_describe_resources(self):
        return Result.new(0x0, "describe resources")

    def do_start_network(self):
        return Result.new(0xFFFF, "start network")
    
    def do_attach_volume(self):
        return Result.new(0xFFFF, "attach volume")

    def do_detach_volume(self):
        return Result.new(0xFFFF, "detach volume")
