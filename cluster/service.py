#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import threading
import socket

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

    def _instances_size(self):
        return len(self._cc_instances)

    def _has_instance(self, inst_id):
        for i in xrange(self._instances_size()):
            if self._cc_instances[i].id == inst_id:
                return i
        return -1

    def _iter_instance(self):
        return iter(self._cc_instances)

    def _get_instance(self, inst_id):
        idx = self._has_instance(inst_id)
        if idx == -1:
            return None
        return self._cc_instances[idx]

    def _add_instance(self, inst):
        if self._has_instance(inst.id) != -1:
            self._logger.warn('instance %s already exists' % (inst.id,))
            return
        self._cc_instances.append(inst)
        self._logger.debug('add instance %s' % (inst.id,))

    def _remove_instance(self, inst_id):
        idx = self._has_instance(inst_id)
        if idx == -1:
            return
        del self._cc_instances[idx]
        self._logger.debug('remove instance %s' % (inst_id,))

    def _thread_monitor(self):
        self._logger.debug("invoked.")
        while True:
            self._logger.debug("wake up")
            self._logger.debug("sleep")
            time.sleep(config.CLUSTER_MONITOR_INTERVAL)

    def _nodes_size(self):
        return len(self._cc_resources)

    def _has_node(self, nid):
        for i in xrange(self._nodes_size()):
            if self._cc_resources[i].id == nid:
                return i
        return -1
    
    def _iter_node(self):
        return iter(self._cc_resources)

    def _get_node(self, nid):
        idx = self._has_node(nid)
        if idx == -1:
            return None
        return self._cc_resources[idx]
    
    def _add_node(self, node_res):
        if self._has_node(node_res.id) != -1:
            self._logger.warn('node %s already exists' % (node_res.id,))
            return
        self._cc_resources.append(node_res)
        self._logger.debug('add node %s' % (node_res.id,))

    def _remove_node(self, nid):
        idx = self._has_node(nid)
        if idx == -1:
            return
        del self._cc_resources[idx]
        self._logger.debug('remove node %s' % (nid,))

    def _add_node_thread(self, nid, ip, port):
        self._logger.debug('invoked')
        node = utils.get_conctrller_object(utils.uri_generator(ip, port))
        with self._nccall_sem:
            rs = node.do_describe_resource()
            if rs.code != 0x0:
                self._logger.warn(res.data['msg'])
                return

        res_data = rs.data
        res_data.update({'uri': uri_generator(ip, port),
                         'id': nid})
        res = ClusterResource(rs.data)

        with self._res_lock:
            if self._has_node(nid) != -1:
                self._logger.warn("already exists node %s" % (nid,))
                return
            self._add_node(res)
            self._logger.info("add node %s" % (nid,))
        self._logger.debug('done')
        
    def _startup_add_node_thread(self, nid, ip, port):
        self._logger.debug('invoked')
        threading.Thread(target=self._add_node_thread, args=(nid, ip, port)).start()
        self._logger.debug('done')

    def do_add_node(self, nid, ip, port):
        self._logger.info('invoked')
        with self._res_lock:
            # node is already in cluster?
            if self._has_node(nid) != -1:
                self._logger.warn('failed to add node %s, %s in node list' % (nid, nid))
                return Result.new(0xFFFF, {'msg': 'failed to add node %s' % (nid,)})
            
            self._startup_add_node_thread(nid)
        self._logger.debug('done')
        return Result.new(0x0, {'msg': 'add node %s' % (nid,)})

    def _vm_exist_on_node(self, nid):
        self._logger.debug('invoked')
        self._logger.debug('done')

    def _terminate_instances(self, inst_ids):
        self._logger.debug('invoked')
        self._logger.debug('done')

    def _get_instances_from_nc(self, nid):
        self._logger.debug('invoked')
        inst_instances = []
        [insts.append(inst) for inst in self._iter_node() if inst.node.id == nid]
        self._logger.debug('done')
        return inst_instances

    def do_remove_node(self, nid, force=False):
        self._logger.info('invoked')
        with self._res_lock:
            if self._has_node(nid) == -1:
                self._logger.warn('node %s is not exists' % (nid,))
                return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))
            if not force:
                if self._vm_exist_on_node(nid):
                    self._logger.warn('failed to remove node %s, some vm running on node %s' % (nid, nid))
                    return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))
            else:
                inst_instances = self._get_instances_from_nc(nid)
                node = self._get_node()
                node_server = utils.get_conctrller_object(node.uri)
                for inst in inst_instances:
                    try:
                        ret = node_server.do_terminate_instance(inst.id)
                    except:
                        self._logger.warn('failed to terminate instance %s' % (inst.id))
            # start remove node
            
            
            
        self._logger.debug('done')
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
