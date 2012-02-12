#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import threading

import config
from common.controller import Controller

class Cluster(Controller):
    ADDR = config.CLUSTER_ADDR
    def __init__(self, is_daemon=True):
        Controller.__init__(self, Cluster.ADDR, "cluster", config.CLUSTER_LOG, config.LOG_LEVEL, is_daemon)
        self._logger.info("initialze controller done")
