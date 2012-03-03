#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import threading

import config
from common.controller import Controller
from common import utils
from common.data import ClusterDetail, ClusterResource, NodeResource, ClusterInstance, Result, InstanceState, NetConfig

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

        self._cc_resources = [] # data.ClusterResourcne
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
        self._logger.debug("invoked")
        if self._has_instance(inst.id) != -1:
            self._logger.warn('instance %s already exists' % (inst.id,))
            return
        self._cc_instances.append(inst)
        self._logger.debug('add instance %s' % (inst.id,))
        self._logger.debug("done")

    def _remove_instance(self, inst_id):
        self._logger.debug("invoked")
        idx = self._has_instance(inst_id)
        if idx == -1:
            return
        del self._cc_instances[idx]
        self._logger.debug('remove instance %s' % (inst_id,))
        self._logger.debug("done")

    def _thread_monitor(self):
        self._logger.debug("invoked.")
        while True:
            self._logger.debug("wake up")
            with self._res_lock:
                self._reflash_node_resources()
            with self._inst_lock:
                self._reflash_instances()
            self._logger.debug("sleep")
            time.sleep(config.CLUSTER_MONITOR_INTERVAL)

    def _reflash_node_resources(self):
        self._logger.debug("invoked")
        [self._reflash_node_resource(res) for res in self._iter_node()]
        self._logger.debug("done")

    def _reflash_instances(self):
        self._logger.debug("invoked")
        [self._reflash_instance(inst) for inst in self._iter_instance()]
        self._logger.debug("done")

    def _change_node_status(self, res, status):
        self._logger.debug('invoked')
        self._logger.info('resource %s change state from %s to %s' % (res.id, res.node_status, status))
        res.node_status = status
        self._logger.debug('done')

    def _reflash_node_resource(self, res):
        self._logger.debug("invoked.")

        node = utils.get_conctrller_object(res.uri)
        try:
            with self._nccall_sem:
                rs = node.do_describe_resource()
            if rs['code']:
                self._logger.warn('failed to connect node %s' % res.id)
                self._change_node_status(res, 'error')
                return
            
            new_res = NodeResource(rs['data']['resource'])
            
            self._change_node_status(res, new_res.node_status)
            res.node_status = new_res.node_status
            res.mem_size_max = new_res.mem_size_max
            res.mem_size_available = new_res.mem_size_available
            res.disk_size_max = new_res.disk_size_max
            res.disk_size_available = new_res.disk_size_available
            res.number_cores_max = new_res.number_cores_max
            res.number_cores_available = new_res.number_cores_available
        except:
            self._change_node_status(res, 'error')

        self._logger.debug("done")

    """ unfinish """
    def _reflash_instance(self, inst):
        self._logger.debug("invoked.")

        res = inst.node
        node = utils.get_conctrller_object(res.uri)
        try:
            rs = node.do_describe_instances([inst.instance_id])
            if rs.code:
                self._logger.warn('failed to get instance %s from node %s' % (inst.instance_id,
                                                                              node.id))
                self._change_node_status(inst, InstanctState.NOSTATE)
                return
        except:
            self._logger.warn('failed to connect node %s' % res.id)
            return

        try:
            new_inst = Instance(rs.data['instances'][0])
        except:
            self._logger.warn('failed to get isntance %s from node %s' % (inst.instance_id,
                                                                          node.id))
            self._change_node_status(inst. InstanceState.NOSTATE)
            return

        inst.state_code = new_inst.state_code
        inst.net = new_inst.net
        inst.volumes = new_inst.volumes

        self._logger.debug("done")

    def _change_instance_state(self, inst, state):
        self._logger.debug('invoked')
        self._logger.info('change instance %s state from %s to %s' % (inst.instance_id,
                                                                      InstanceState.state_name(inst.state_code),
                                                                      InstanceState.state_name(state)))
        inst.state_code = InstanceState.NOSTATE
        self._logger.debug('done')

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
            try:
                rs = node.do_describe_resource()
                if rs['code'] != 0x0:
                    self._logger.warn(rs.data['msg'])
                    return
            except Exception, err:
                self._logger.warn(err)
                return

        res_data = rs['data']
        res_data.update({'uri': utils.uri_generator(ip, port),
                         'id': nid})
        res = ClusterResource(rs['data'])

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
            
            self._startup_add_node_thread(nid, ip, port)
        self._logger.debug('done')
        return Result.new(0x0, {'msg': 'add node %s' % (nid,)})

    def _instance_on_node(self, nid):
        self._logger.debug('invoked')
        for inst in self._iter_instance():
            if inst.node.id == nid:
                return
        self._logger.debug('done')
        return False

#    #unimplement
#    def _terminate_instances(self, inst_ids):
#        self._logger.debug('invoked')
#        self._logger.debug('done')

    def _startup_terminate_instances(self, inst_ids):
        # what a BAICHI action!!!
        thread = utils.ResultThread(self.do_terminate_instances, inst_ids)
        thread.start()
        thread.join()
        return thread.result

    def _get_instances_on_node(self, nid):
        self._logger.debug('invoked')
        inst_instances = []
        [inst_instances.append(inst) for inst in self._iter_node() if inst.node.id == nid]
        self._logger.debug('done')
        return inst_instances

    def do_remove_node(self, nid, force=False):
        self._logger.info('invoked')
        with self._res_lock:
            if self._has_node(nid) == -1:
                self._logger.warn('node %s is not exists' % (nid,))
                return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))
            if not force:
                if self._instance_exist_on_node(nid):
                    self._logger.warn('failed to remove node %s, some vm running on node %s' % (nid, nid))
                    return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))
            else:
                # if force is true, find all instance which is running on node
                insts = self._get_instance_on_node(nid)
                inst_ids = [inst.instance_id for inst in insts]
        
        if force:
            with self._nccall_sem:
                self._logger.info('terminate instances:', inst_ids)
                ret = self._startup_terminate_instances(inst_ids)
                if ret.code != 0x0:
                    self._logger.error('failed to remove node %s, terminate vm failed' % (nid,))
                    return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))

        with self._res_lock:
            self._logger.info('remove node %s' % nid)
            self._remove_node(nid)
            
        self._logger.debug('done')
        return Result.new(0x0, "remove node %s" % nid)

    def do_power_down(self):
        return Result.new(0x0, "power down")

    def do_terminate_instances(self):
        return Result.new(0x0, "terminate instances")

    def do_describe_instances(self):
        return Result.new(0x0, "describe instances")

    def _schedule_instance(self, param, target_node_id=None):

        policy = target_node_id and "explicit" or config.DEFAULT_SCHEDULE_POLITY

        try:
            return getattr(self, '_schedule_instance_' + policy)(param, target_node_id)
        except:
            self._logger.critical('instance schedule function not found, please fix config')
            sys.exit(255)

    def _iter_running_node(self):
        return [res for res in self._iter_node() if res.node_status == "ok"]

    def _node_resource_point(self, res):
        return res.number_cores_available * config.CORES_POINT_PER_COUNT + res.mem_size_available * config.MEMORY_POINT_PER_GB + res.disk_size_available * config.DISK_POINT_PER_GB

    def _verify_resource(self, param, res):
        lack_list = []
        if res.number_cores_available < param.cores:
            lack_list.append('cores')
        if res.mem_size_available < param.memory:
            lack_list.append('memory')
        if res.disk_size_available < param.disk:
            lack_list.append('disk')
        return lack_list

    def _schedule_instance_greed(self, param, _=None):
        return self._schedule_instance_by_func(lambda x,y: x<y)

    def _schedule_instance_smart(self, param, _=None):
        return self._schedule_instance_by_func(lambda x,y: x>y)

    def _schedule_instance_by_func(self, func):
        def warpper(param, _=None):
            point = 0
            perfect_res = None
            for res in self._iter_running_node():
                if not self._verify_resource(param, res):
                    cur_point = self._node_resource_point(res)
                    if func(cur_point, point):
                        point = cur_point
                        perfect_res = res
            return perfect_res
        return warpper

    def _schedule_instance_explicit(self, param, target_node):
        try:
            return [res for res in self._iter_running_node() if res.id == target_node and not self._verify_resource(param, res)][0]
        except:
            return None
    
    def _verify_resource(self, param, res):
        lack = []
        if res.number_cores_available - param.cores < 0:
            lack.append("cpu")
        if res.mem_size_available - param.mem < 0:
            lack.append("memory")
        if res.disk_size_available - param.disk < 0:
            lack.append("disk")
        return lack

    def _run_instance_thread(self, 
                             instance_id,
                             reservation_id,
                             param_t,
                             image_id, image_url,
                             kernel_id, kernel_url,
                             ramdisk_id, ramdisk_url,
                             net_config,
                             user_id,
                             target_node_id):
        self._logger.debug('invoked')

        res = self._get_node(target_node_id)
        node_server = utils.get_conctrller_object(res.uri)

        start_time = time.time()
        res = Result()
        while res.code and (time.time() - start_time < config.CLUSTER_WAKE_THRESH):
            res = node_server.do_run_instance(instance_id,
                                              reservation_id,
                                              param_t,
                                              image_id, image_url,
                                              kernel_id, kernel_url,
                                              ramdisk_id, ramdisk_url,
                                              net_config,
                                              user_id)
            if res.code:
                time.sleep(1)
        
        if res.code:
            self._logger.warn('failed to run instance: %s' % instance_id)
            return 1

        inst = ClusterInstance.new_instance(instance_id,
                                            reservation_id,
                                            param_t,
                                            image_id, image_url,
                                            kernel_id, kernel_url,
                                            ramdisk_id, ramdisk_url,
                                            InstanceState.PENDING,
                                            net_config,
                                            user_id,
                                            self._get_node(target_node_id))

        with self._inst_lock:
            self._add_instance(inst)

        with self._res_lock:
            node = self._get_node(target_node_id)
            node.mem_size_available -= param_t.mem
            node.number_cores_available -= param_t.number_cores_available
            node.disk_size_available -= param_t.disk_size_available

        self._logger.debug('done')

    def _startup_run_instances_thread(self,
                                      instnce_ids,
                                      reservation_id,
                                      user_id,
                                      params_t,
                                      image_id, image_url,
                                      kernel_id, kernel_url,
                                      ramdisk_id, ramdisk_url,
                                      net_configs,
                                      target_node_id):
        self._logger.debug('invoked')

        for i in xrange(len(instnce_ids)):
            nid = self._schedule_instance(params_t, target_node_id)
            self._run_instance_thread(instnce_ids[i],
                                      reservation_id,
                                      params_t,
                                      image_id, image_url,
                                      kernel_id, kernel_url,
                                      ramdisk_id, ramdisk_url,
                                      net_configs[i],
                                      user_id,
                                      nid)

        self._logger.debug('done')

    def do_run_instances(self, 
                         instance_ids,
                         reservation_id,
                         user_id,
                         params_t,
                         image_id, image_url,
                         kernel_id, kernel_url,
                         ramdisk_id, ramdisk_url,
                         mac_addrs,
                         target_node_id=None):
        self._logger.info('invoked')

        verify_run_instances_arguments = lambda: len(instance_ids) == len(mac_addrs) and self._has_node(target_node_id) != -1

        # verify arguments
        if not self._verify_run_instances_arguments():
            self._logger.error('error arguments')
            return Result.new(0xFFFF, 'failed to run instances')
        
        # setup NetConfig
        net_configs = [NetConfig.new_instance(mac=mac) for mac in mac_addrs]

        self._startup_run_instances_thread(instance_ids,
                                           reservation_id,
                                           user_id,
                                           params_t,
                                           image_id, image_url,
                                           kernel_id, kernel_url,
                                           ramdisk_id, ramdisk_url,
                                           net_configs,
                                           target_node_id)
                
        self._logger.debug('done')
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
