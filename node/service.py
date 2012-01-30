#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import threading
import libvirt

import config
from common import utils
from common.controller import Controller
from common import data
from common.data import Result
from common.data import InstanceState

class Node(Controller):
    ADDR = config.NODE_ADDR
    def __init__(self, is_daemon=True):
        # initialize controller
        Controller.__init__(self, Node.ADDR, "node", config.NODE_LOG, config.LOG_LEVEL, is_daemon)
        self._logger.info("ippnitialze controller done")
        
        # 0 no _initialized, 1 has been _initialized, -1 _initialized error or initialing. 
        self._initialized = 0
        self._global_instances = None
        self._nc_detail = None
        
        self._hyp_lock = None
        self._inst_lock = None
        self._res_lock = None
        
        self._monitor_thread = None
        
    def _init_node(self):
        # check node is _initialized
        if self._initialized > 0:
            return 0
        elif self._initialized < 0:
            return -1
        
        # startup to initialize
        self._initialized = -1

        self._global_instances = []
        self._nc_detail = data.NodeDetail()

        # initialize lock object
        self._hyp_lock = utils.Lock()
        self._inst_lock = utils.Lock()
        self._res_lock = utils.Lock()

        # initialize node resource
        self._initialize()

        # adopt instances
        self._adopt_instances()

        # startup monitor thread
        self._monitor_thread = threading.Thread(target=self._thread_monitor, args=())
        self._monitor_thread.setDaemon(True)
        self._startup_monitor_thread()

        # _init_node done. set self._initialized to 1
        self._initialized = 1

    def _adopt_instances(self): pass        

    def start(self):
        # _initialized node detail
        self._logger.info("initialize node detail")
        
        rs = self._init_node()
        if rs == 1:
            self._logger.error("node has _initialized")
            sys.exit(1)
        elif rs == -1:
            self._logger.critical("startup node failed")
            sys.exit(1)
        self._logger.debug("initialize node detail done")
        
        # startup service
        self._logger.info("starting service")
        super(Node, self).start()
        self._logger.debug("start service done")
        
        # add iptable rule
        # iptables -A FORWARD -p UDP --sport 67:68 --dport 67:68 -j LOG --log-level 0
        (status, _output) = commands.getstatusoutput("echo '%s' | sudo -S iptables -A FORWARD -p UDP --sport 67:68 --dport 67:68 -j LOG --log-level 0" % config.NODE_PASSWD)
        if status:
            self._logger.error("failed to run iptable, please check your config password.")
            sys.exit(1)
        self._logger.info("add iptable rule.")        
        
    def stop(self):
        self._logger.debug("invoked")
        super(Node, self).stop()
        self._logger.debug("done")
        return Result.new(0x0, "stop service")

    def _initialize(self):
        self._logger.debug("invoked.")
        # get system information
        (stat, output) = commands.getstatusoutput("get_sys_info")
        if stat:
            self._logger.error("get system information failed")
            sys.exit(1)

        rs_cores = utils.get_vale_from_outpout(output, "nr_cores")
        rs_cores = int(rs_cores)
        
        rs_mem = utils.get_vale_from_outpout(output, "total_memory")
        rs_mem = int(rs_mem)
        
        if rs_cores == -1 or rs_mem == -1:
            self._logger.error("get system information failed")
            sys.exit(1)
        
        self._nc_detail.uri = config.LIBVIRT_CONNECTION
        
        self._res_lock.acquire()
        
        # cores = physics_cores * weight
        self._nc_detail.config_max_cores = rs_cores * config.NODE_WEIGHT
        self._nc_detail.cores_max = self._nc_detail.config_max_cores
        
        # 256MB for system use
        self._nc_detail.config_max_mem = utils.kb2mb(rs_mem) - config.NODE_RESERVE_MEM
        self._nc_detail.mem_max = self._nc_detail.config_max_mem
        
        # set 0
        self._nc_detail.config_max_disk = self._nc_detail.disk_max = 0

        self._res_lock.release()

        self._logger.debug("done")

    def _check_connect(self):
        if self._nc_detail.vir_conn == None or \
        self._nc_detail.vir_conn.getURI() == None:
            try:
                self._nc_detail.vir_conn = libvirt.open(self._nc_detail.uri)
            except:
                self._logger.error("Failed to connect libvirt")
                return None
        return self._nc_detail.vir_conn

    def _startup_monitor_thread(self):
        self._logger.debug("invoked.")
        
        self._monitor_thread.start()
        
    def _thread_monitor(self):
        self._logger.debug("invoked.")
        while True:
            now = time.time()            
            self._logger.debug("monitor thread running...")
            self._inst_lock.acquire()
            
            for inst in self._iter_global_instances():
                self._refresh_instance_detail(inst)
                
                if inst.state_code != InstanceState.BOOTING and\
                   inst.state_code != InstanceState.SHUTOFF and\
                   inst.state_code != InstanceState.SHUTDOWN and\
                   inst.state_code != InstanceState.TEARDOWN:
                    continue
                
                if inst.state_code == InstanceState.TEARDOWN:
                    if now - inst.termination_time > config.TEARDOWN_STATE_DURATION:
                        self._remove_instance(inst.instance_id)
                        self._logger.info("forgetting about instance %s" % inst.instance_id)
                    continue
                
                if inst.state_code == InstanceState.BOOTING and\
                   (now - inst.boot_time) < config.BOOTING_CLEANED_THRESHOLD: continue
                
                # i need to release some resource
                
                # free resource
                self._res_lock.acquire()
                self._free_resource(inst.params)
                self._res_lock.release()

                
                # change instance state to teardown, all resource has been release
                self._change_instance_state(inst, InstanceState.TEARDOWN)
                inst.termination_time = time.time()
                                
            self._inst_lock.release()
            time.sleep(config.NODE_MONITOR_INTERVAL)
            
    def _add_instance(self, inst):        
        if self._has_instance(inst.instance_id) != -1:
            self._logger.warn("failed to add instance %s, %s in instance list." % (inst.instance_id,
                                                                                   inst.instance_id))
            return
        
        self._global_instances.append(inst)
        self._logger.debug("add instance %s" % (inst.instance_id,))
    
    def _remove_instance(self, instance_id):
        idx = self._has_instance(instance_id)
        if idx == -1:
            return
        self._global_instances.remove(self._global_instances[idx])
        self._logger.debug("remove instance %s" % (instance_id,))

    def _global_instances_size(self):
        return len(self._global_instances)
        
    def _has_instance(self, instance_id):
        for i in xrange(self._global_instances_size()):
            inst_t = self._global_instances[i]
            if inst_t.instance_id == instance_id:
                return i
        return -1
    
    def _get_instance(self, instance_id):
        idx = self._has_instance(instance_id)
        if idx == -1:
            return None
        return self._global_instances[idx]

    def _iter_global_instances(self):
        return iter(self._global_instances)        


    
    def _allocate_resource(self, params): #data.VirtualMachine
        
        if params.mem <= self._nc_detail.mem_max and \
           params.cores <= self._nc_detail.cores_max and \
           params.disk <= self._nc_detail.disk_max:
            self._nc_detail.mem_max -= params.mem
            self._nc_detail.cores_max -= params.cores
            self._nc_detail.disk_max -= params.disk
        else:
            return -1
        
        self._print_resource()

        return 0
    
    def _free_resource(self, params):
        
        self._nc_detail.mem_max = self._nc_detail.mem_max + params.mem
        self._nc_detail.mem_max = self._nc_detail.mem_max > self._nc_detail.config_max_mem and\
                                  self._nc_detail.config_max_mem or\
                                  self._nc_detail.mem_max
            
        self._nc_detail.cores_max = self._nc_detail.cores_max + params.cores
        self._nc_detail.cores_max = self._nc_detail.cores_max > self._nc_detail.config_max_cores and\
                                    self._nc_detail.config_max_cores or\
                                    self._nc_detail.cores_max
            
        self._nc_detail.disk_max = self._nc_detail.disk_max + params.disk
        self._nc_detail.disk_max = self._nc_detail.disk_max > self._nc_detail.config_max_disk and\
                                   self._nc_detail.disk_max or\
                                   self._nc_detail.config_max_disk
                
        self._print_resource()
        return 0

    def _print_resource(self):
        self._logger.info("""current resource:\nconfig_max_disk=%d, disk_max=%d\nconfig_max_mem=%d, mem_max=%d\nconfig_max_cores=%d, cores_max=%d""" % 
                          (self._nc_detail.config_max_disk, self._nc_detail.disk_max,
                           self._nc_detail.config_max_mem, self._nc_detail.mem_max,
                           self._nc_detail.config_max_cores, self._nc_detail.cores_max))
    

    
    def _startup_instance_thread(self, inst):
        self._logger.debug("invoked")
        
        threading.Thread(target=self._thread_run_instance, args=(inst,)).start()
        
    def _thread_run_instance(self, inst):
        self._logger.debug("invoked")
        
        # check connection
        if not self._check_connect():
            self._logger.error("could not start instance %s, abandoning it." % inst.instance_id)
            inst.state_code = InstanceState.SHUTOFF
            return

        # check network
        # pass
        
        # check image detail
        # if false, change state to teardown
        
        # gen libvirt xml
        
        # print running instance?
        self._print_running_instances()
        
        # startup instance from libvirt
        inst.boot_time = time.time()
        
        # change instance state to booting
        self._change_instance_state(inst, InstanceState.BOOTING)
        inst.boot_time = time.time()
        
        self._logger.info("instance %s startup." % inst.instance_id)
        
    def _print_running_instances(self):
        count = 0
        [+ +count for inst in self._iter_global_instances() if inst.state_code in 
         (InstanceState.RUNNING,
          InstanceState.PAUSED,
          InstanceState.BLOCKED)]
        self._logger.info("running instances: %d" % (count,))
        self._logger.debug("_global_instances count: %d" % (self._global_instances_size(),))
    
    def _refresh_instance_detail(self, inst):
        
        # refresh instance state
        now = inst.state_code
        
        if now == InstanceState.TEARDOWN:
            return
        
        if self._check_connect() == None:
            return

        # try to lookup instance
        try:
            self._hyp_lock.acquire()
            dom = self._nc_detail.vir_conn.lookupByName(inst.instance_id)
            self._hyp_lock.release()
        except:
            if now == InstanceState.RUNNING or \
               now == InstanceState.BLOCKED or \
               now == InstanceState.PAUSED or \
               now == InstanceState.SHUTDOWN:
                self._logger.warn("Failed to find %s in node." % inst.instance_id)
                self._change_instance_state(inst, InstanceState.SHUTOFF)
            return

        # try to get instance state
        try:
            self._hyp_lock.acquire()
            info = dom.info()
            self._hyp_lock.release()
        except:
            self._logger.warn("Failed to get informations from domain %s" % inst.instance_id)
            return

        xen = info[0]
        
        if now in (InstanceState.BOOTING,
                   InstanceState.RUNNING,
                   InstanceState.BLOCKED,
                   InstanceState.PAUSED):
            if now != xen:
                self._change_instance_state(inst, xen)
        elif now in (InstanceState.SHUTOFF,
                     InstanceState.SHUTDOWN,
                     InstanceState.CRASHED):
            if xen in (InstanceState.RUNNING,
                       InstanceState.BLOCKED,
                       InstanceState.PAUSED):
                self._logger.warn("detected prodigal domain %s, terminating it" % inst.instance_id)
                # should i acquire a lock?
                # yes, i shoud acquire a hyp-lock
                self._hyp_lock.acquire()
                dom.destroy()
                self._hyp_lock.release()
            else:
                self._change_instance_state(inst, xen)
        else:
            self._logger.error("unknown state (%d) for instance" % now)
        
        # refresh instance ip
        if inst.instance_id not in (InstanceState.RUNNING,
                                    InstanceState.BLOCKED,
                                    InstanceState.PAUSED):
            return

        if inst.net_config.ip != "0.0.0.0":
            return
        
        self._logger.debug("lookup instance %s ip from mac: %s" % \
                           (inst.instance_id, inst.net_config.mac))
        ip = self._discover_ip_from_mac(inst.net_config.mac)
        if ip is "0.0.0.0":
            return
        inst.net_config.ip = ip
        self._logger.info("domain %s discover ip: %s" % \
                          (inst.instance_id, inst.net_config.ip))
        
    def _discover_ip_from_mac(self, mac):
        # lookup ip from /proc/net/arp
        CMD = "populate_arp"
        ARP_PATH = "/proc/net/arp"
        (status, _output) = commands.getstatusoutput(CMD)
        if status:
            self._logger.warn("failed to execute script: %s" % (CMD,))

        try:
            f = open(ARP_PATH)
            f.readline()
            
            line = f.readline()
            while line:
                (ip_t, _hw, _flags, mac_t, _mask, _dev) = line.split()
                if mac_t == mac:
                    return ip_t
        finally:
            f.close()
        
        return "00:00:00:00"
        
    def _change_instance_state(self, inst, state):
        self._logger.debug("instance %s change to %s from %s" % \
                           (inst.instance_id, \
                            InstanceState.state_name(state), \
                            InstanceState.state_name(inst.state_code)))
        inst.state_code = state
    
    def _find_and_terminate_instance(self, instance_id, destroy):
        idx = self._has_instance(instance_id)
        if idx == -1:
            # instance not found
            return None
        
        inst = self._get_instance(instance_id)
        
        conn = self._check_connect()
        if conn == None:
            # failed to connect
            return inst
        
        try:
            self._hyp_lock.acquire()
            dom = conn.lookupByName(instance_id)
        except libvirt.libvirtError:
            # failed to lookup instance
            if inst.state_code != InstanceState.BOOTING and\
               inst.state_code != InstanceState.TEARDOWN:
                self._logger.warn("domain %s to be terminated not running on hypervisor", (instance_id,))
            return inst
        finally:
            self._hyp_lock.release()
        
        try:
            self._hyp_lock.acquire()
            if destroy:
                ret = dom.destroy()
            else:
                ret = dom.shutdown()
        except:
            # failed to destroy or shutdown instance
            return inst
        finally:
            self._hyp_lock.release()
        
        LOG_STR = " domain for instance %s" % (instance_id, )
        if not ret:
            if destroy:
                LOG_STR = "destroyed" + LOG_STR
            else:
                LOG_STR = "shutting down" + LOG_STR
        self._logger.warn(LOG_STR)
        
        return inst
    
    def do_power_down(self):
        return Result.new(0x0, 'power down')
    
    def do_terminate_instance(self, instance_id):
        try:
            self._inst_lock.acquire()
            inst = self._find_and_terminate_instance(instance_id, 1)
            if inst == None:
                return Result.new(0xFFFFFFFF, "instance not found")
            
            if inst.state_code != InstanceState.TEARDOWN:
                self._change_instance_state(inst, InstanceState.SHUTOFF)
        finally:
            self._inst_lock.release()
                    
        return Result.new(0x0, 'terminate instance')

    def do_describe_instances(self):
        return Result.new(0x0, 'describe instances')

    def do_run_instance(self,
                        instance_id,
                        reservation_id,
                        params, # data.VirtualMachine
                        image_id, image_url,
                        kernel_id, kernel_url,
                        ramdisk_id, ramdisk_url,
                        net_config, # data.NetConfig
                        user_id):
        self._inst_lock.acquire()
        idx = self._has_instance(instance_id)
        self._inst_lock.release()
        if idx != -1:
            self._logger.error("instance %s is already running." % instance_id)
            return Result.new(0xFFFFFFFF, "failed to startup instance %s" % (instance_id,))

        
        params_t = data.VirtualMachine(params)
        net_config_t = data.NetConfig(net_config)
        
        inst = data.Instance.new_instance(instance_id,
                                          reservation_id,
                                          params_t,
                                          image_id, image_url,
                                          kernel_id, kernel_url,
                                          ramdisk_id, ramdisk_url,
                                          InstanceState.PENDING,
                                          net_config_t,
                                          user_id)
        try:
            self._res_lock.acquire()
            if self._allocate_resource(inst.params):
                self._logger.warn("failed to allocate resource")
                return Result.new(0xFFFFFFFF, "failed to allocate resource")
        finally:
            self._res_lock.release()

        self._inst_lock.acquire()
        self._add_instance(inst)
        self._inst_lock.release()
        
        self._startup_instance_thread(inst)
        
        return Result.new(0x0, "run instance")    
    
    def do_reboot_instance(self):
        return Result.new(0x0, 'reboot instance')

    def do_get_console_output(self):
        return Result.new(0x0, 'get console output')

    def do_describe_resource(self):
        return Result.new(0x0, 'describe resource')

    def do_start_network(self):
        return Result.new(0x0, 'start network')

    def do_attach_volume(self): 
        return Result.new(0x0, 'attache volume')

    def do_detach_volume(self): 
        return Result.new(0x0, 'detach volume')
