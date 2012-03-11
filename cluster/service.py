#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import threading

import config
from common.controller import Controller
from common import utils
from common.data import ClusterDetail, ClusterResource, NodeResource, ClusterInstance, Instance, Result, InstanceState, NetConfig, VirtualMachine

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

    def _instances_size(self):
        return len(self._cc_instances)


    def _has_instance(self, inst_id):
        for i in xrange(self._instances_size()):
            if self._cc_instances[i].instance_id == inst_id:
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
        if self._has_instance(inst.instance_id) != -1:
            self._logger.warn('instance %s already exists' % (inst.id,))
            return
        self._cc_instances.append(inst)
        self._logger.debug('add instance %s' % (inst.instance_id,))
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
                self._reflash_cluster_detail()
            with self._inst_lock:
                self._reflash_instances()
            self._logger.debug("sleep")
            time.sleep(config.CLUSTER_MONITOR_INTERVAL)


    def _reflash_node_resources(self):
        self._logger.debug("invoked")
        [self._reflash_node_resource(res) for res in self._iter_node()]
        self._logger.debug("done")

    def _reflash_cluster_detail(self):
        def reflash():
            self._cc_detail.config_max_cores += res.number_cores_available
            self._cc_detail.config_max_mem += res.mem_size_available
            self._cc_detail.config_max_disk += res.disk_size_available
            self._cc_detail.cores_max += res.number_cores_max
            self._cc_detail.mem_max += res.mem_size_max
            self._cc_detail.disk_max += res.disk_size_max
            
        self._logger.debug('invoked')
        
        detail = ClusterDetail()
        detail.uri = self._cc_detail.uri
        detail.sched_policy = self._cc_detail.sched_policy
        detail.sched_state = self._cc_detail.sched_state
        self._cc_detail = detail
        
        [reflash() for res in self._iter_node()]
        
        self._logger.debug('done')

    def _reflash_instances(self):
        self._logger.debug("invoked")
#        [self._reflash_instance(inst) for inst in self._iter_instance()]
        reflash_map = {}
        for inst in self._iter_instance():
            if not reflash_map.has_key(inst.node):
                reflash_map[inst.node] = []
            reflash_map[inst.node].append(inst)
        [self._reflash_instances_by_list(insts) for insts in reflash_map.values()]
        self._logger.debug("done")


    def _reflash_instances_by_list(self, insts):

        if not isinstance(insts, list) or len(insts) == 0:
            return
        
        inst_ids = []
        [inst_ids.append(inst.instance_id) for inst in insts]
        
        try:
            node = utils.get_conctrller_object(insts[0].node.uri)
            with self._nccall_sem:
                rs = node.do_describe_instances(inst_ids)
            if rs['code']:
                self._logger.warn('failed to reflash instances: %s' % str(inst_ids))
                return
        except:
            self._logger.warn('failed to connect node %s' % insts[0].node.uri)


        data_instances = rs['data']['instances']
        new_instances_map = {}
        for data_inst in data_instances:
            new_inst = Instance(data_inst)
            new_instances_map[new_inst.instance_id] = new_inst

        [self._reflash_instance(inst, new_instances_map.get(inst.instance_id, None)) for inst in insts]
        

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


    def _reflash_instance(self, inst, new_inst):
        self._logger.debug('invoked')

        if not new_inst:
            self._remove_instance(inst.instance_id)
            self._logger.info('instance %s not found on %s, remove it' % (inst.instance_id,
                                                                          inst.node.id))
            return

        self._logger.info('reflash instance %s' % inst.instance_id)

        self._change_instance_state(inst, new_inst.state_code)
        inst.net = new_inst.net
        inst.volumes = new_inst.volumes

        self._logger.debug('done')


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
        try:
            with self._nccall_sem:
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


    def _instance_on_node(self, nid):
        self._logger.debug('invoked')
        for inst in self._iter_instance():
            if inst.node.id == nid:
                return
        self._logger.debug('done')
        return False


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
        return res.number_cores_available * config.CORES_POINT_PER_COUNT + res.mem_size_available * config.MEMORY_POINT_PER_MB + res.disk_size_available * config.DISK_POINT_PER_MB


    def _verify_resource(self, param, res):
        lack_list = []
        if res.number_cores_available < param.cores:
            lack_list.append('cores')
        if res.mem_size_available < param.mem:
            lack_list.append('memory')
        if res.disk_size_available < param.disk:
            lack_list.append('disk')
        return lack_list


    def _schedule_instance_greed(self, param, _=None):
        return self._schedule_instance_by_func(lambda x,y: x<y)(param, _)


    def _schedule_instance_smart(self, param, _=None):
        return self._schedule_instance_by_func(lambda x,y: x>y)(param, _)


    def _schedule_instance_by_func(self, func):
        def warpper(param, _=None):
            point = 0
            perfect_res = None
            for res in self._iter_running_node():
                if not self._verify_resource(param, res):
                    cur_point = self._node_resource_point(res)
                    if not perfect_res or func(cur_point, point):
                        point = cur_point
                        perfect_res = res
            return perfect_res and perfect_res.id or None
        return warpper


    def _schedule_instance_explicit(self, param, target_node):
        try:
            return ([res for res in self._iter_running_node() if res.id == target_node and not self._verify_resource(param, res)][0]).id
        except:
            return None

    
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

        rs = {'code': 0xFFFF}
        while rs['code'] and (time.time() - start_time < config.CLUSTER_WAKE_THRESH):
            with self._nccall_sem:
                rs = node_server.do_run_instance(instance_id,
                                                 reservation_id,
                                                 param_t,
                                                 image_id, image_url,
                                                 kernel_id, kernel_url,
                                                 ramdisk_id, ramdisk_url,
                                                 net_config,
                                                 user_id)
            if rs['code']:
                time.sleep(1)
        
        if rs['code']:
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
            node.number_cores_available -= param_t.cores
            node.disk_size_available -= param_t.disk

        self._logger.debug('done')


    def _startup_run_instances_thread(self,
                                      instance_ids,
                                      reservation_id,
                                      user_id,
                                      params_t,
                                      image_id, image_url,
                                      kernel_id, kernel_url,
                                      ramdisk_id, ramdisk_url,
                                      net_configs,
                                      target_node_id):
        self._logger.debug('invoked')

        for i in xrange(len(instance_ids)):
            nid = self._schedule_instance(params_t, target_node_id)
            if nid == None:
                self._logger.warn('failed to start instance %s, not enough resource' % instance_ids[i])
                return
                
            self._run_instance_thread(instance_ids[i],
                                      reservation_id,
                                      params_t,
                                      image_id, image_url,
                                      kernel_id, kernel_url,
                                      ramdisk_id, ramdisk_url,
                                      net_configs[i],
                                      user_id,
                                      nid)

        self._logger.debug('done')


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
                    self._logger.warn('failed to remove node %s, terminate vm failed' % (nid,))
                    return Result.new(0xFFFF, 'failed to remove node %s' % (nid,))

        with self._res_lock:
            self._logger.info('remove node %s' % nid)
            self._remove_node(nid)
            
        self._logger.debug('done')
        return Result.new(0x0, "remove node %s" % nid)


    def do_power_down(self):
        return Result.new(0x0, "power down")


    def do_terminate_instances(self, inst_ids):
        self._logger.info('invoked')
        if not isinstance(inst_ids, list):
            self._logger.warn('error arguments')
            return Result.new(0x0, {'msg': 'error arguments'})

        [self._find_and_terminate_instance(inst_id) for inst_id in inst_ids]

        self._logger.info('done')
        return Result.new(0x0, 'terminate instances')

    def _find_and_terminate_instance(self, inst_id):
        self._logger.debug('invoked')

        inst = self._get_instance(inst_id)
        if inst == None:
            self._logger.warn('instance %s do not exists on cluster' % inst_id)
            return

        node = utils.get_conctrller_object(inst.node.uri)
        try:
            with self._nccall_sem:
                rs = node.do_terminate_instance(inst_id)
            if rs['code'] != 0:
                self._logger.warn('failed to terminate instance %s on node %s' % (inst_id, inst.node.id))
                return
        except:
            self._logger.warn('failed to connect node %s' % inst.node.id)
            return

        self._logger.debug('done')

    def do_describe_instances(self):
        return Result.new(0x0, "describe instances")


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

        verify_run_instances_arguments = lambda: len(instance_ids) == len(mac_addrs) and self._has_node(target_node_id) == -1

        # verify arguments
        if not verify_run_instances_arguments():
            self._logger.wran('error arguments')
            return Result.new(0xFFFF, 'failed to run instances')
        
        # setup NetConfig
        net_configs = [NetConfig.new_instance(mac=mac) for mac in mac_addrs]
        param = VirtualMachine(params_t)

        self._startup_run_instances_thread(instance_ids,
                                           reservation_id,
                                           user_id,
                                           param,
                                           image_id, image_url,
                                           kernel_id, kernel_url,
                                           ramdisk_id, ramdisk_url,
                                           net_configs,
                                           target_node_id)
                
        self._logger.debug('done')
        return Result.new(0x0, "run instances")


    def do_reboot_instances(self, inst_ids):
        self._logger.info('invoked')

        if not isinstance(inst_ids, list):
            self._logger.warn('error arguments')
            return Result.new(0xFFFF, {'msg': 'error arguments'})
        
        [self._find_and_reboot_instance(inst_id) for inst_id in inst_ids]

        self._logger.debug('done')
        return Result.new(0x0, "reboot instances")

    def _find_and_reboot_instnce(self, inst_id):
        self._logger.debug('invoked')

        inst = self._get_instance(inst_id)
        if inst == None:
            self._logger.warn('instance %s do not exists on cluster' % inst_id)
            return

        node = utils.get_conctrller_object(inst.node.uri)
        try:
            with self._nccall_sem:
                rs = node.do_reboot_instance(inst_id)
            if rs['code'] != 0:
                self._logger.warn('failed to reboot instance %s on node %s' % (inst_id, inst.node.id))
                return
        except:
            self._logger.warn('failed to connect node %s' % inst.node.id)
            return
        
        self._logger.debug('done')

    def do_get_console_output(self):
        return Result.new(0x0, "console output")


    def do_describe_resources(self):
        self._logger.info('invoked')

        self._logger.debug('done')
        return Result.new(0x0, "describe resources")


    def do_start_network(self):
        return Result.new(0xFFFF, "start network")

    
    def do_attach_volume(self):
        return Result.new(0xFFFF, "attach volume")


    def do_detach_volume(self):
        return Result.new(0xFFFF, "detach volume")
