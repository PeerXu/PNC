#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

class Metadata:
    correlation_id = ""
    user_id = ""
    
    def __init__(self, data={}):
        if not data:
            return
        self.correlation_id = data["correlation_id"]
        self.user_id = data["user_id"]

class VirtualMachine:
    mem = 0
    cores = 0
    disk = 0
    #dev_mapping = None
    
    def __init__(self, data={}):
        if not data:
            return
        self.mem = data["mem"]
        self.cores = data["cores"]
        self.disk = data["disk"]
    
class NetConfig:
    ip = "0.0.0.0"
    mac = "00:00:00:00:00:00"
    
    def __init__(self, data={}):
        if not data:
            return 
        self.ip = data["ip"]
        self.mac = data["mac"]

class Volume:
    volume_id = ""
    remote_dev = ""
    local_dev = ""
    local_dev_real = ""
    state_code = 0
    
    def __init__(self, data={}):
        if not data:
            self.volume_id = data["volume_id"]
            self.remote_dev = data["remote_dev"]
            self.local_dev = data["local_dev"]
            self.local_dev_real = data["local_dev_real"]
            self.state_code = data["state_code"]

class Instance:
    instance_id = ""
    image_id = ""
    image_url = ""
    kernel_id = ""
    kernel_url = ""
    ramdisk_id = ""
    ramdisk_url = ""
    reservation_id = ""
    user_id = ""
    state_code = 0 # RunInstance request arrival
    launch_time = 0 # STARTING -> BOOTING transition
    termination_time = 0 # when resources are release (-> TRERDOWN transtion)
    boot_time = 0
    params = None # value of VirtualMachine
    net = None # value of NetConfig
    volumes = [] # value of Volume
    
    def __init__(self, data={}):
        if not data:
            return 
        self.instance_id = data["instance_id"]
        self.image_id = data["image_id"]
        self.image_url = data["image_url"]
        self.kernel_id = data["kernel_id"]
        self.kernel_url = data["kernel_url"]
        self.ramdisk_id = data["ramdisk_id"]
        self.ramdisk_url = data["ramdisk_url"]
        self.reservation_id = data["reservation_id"]
        self.user_id = data["user_id"]
        self.state_code = data["state_code"]
        self.launch_time = data["launch_time"]
        self.termination_time = data["termination_time"]
        self.boot_time = data["boot_time"]
        self.params = VirtualMachine(data["params"])
        self.net = NetConfig(data["net"])
        self.volumes = [Volume(dat) for dat in data["volumes"]]
        
    @staticmethod
    def new_instance(instance_id,
                     reservation_id,
                     params,
                     image_id, image_url,
                     kernel_id, kernel_url,
                     ramdisk_id, ramdisk_url,
                     state,
                     net_config,
                     user_id):
        
        inst = Instance()
        
        inst.instance_id = instance_id
        inst.reservation_id = reservation_id
        inst.params = params
        inst.image_id = image_id
        inst.image_url = image_url
        inst.kernel_id = kernel_id
        inst.kernel_url = kernel_url
        inst.ramdisk_id = ramdisk_id
        inst.ramdisk_url = ramdisk_url
        inst.state_code = state
        inst.net = net_config
        inst.user_id = user_id

        return inst
        
class Resource:
    node_status = ""
    mem_size_max = 0
    mem_size_available = 0
    disk_size_max = 0
    disk_size_available = 0
    number_cores_max = 0
    number_cores_available = 0
    
    def __init__(self, data={}):
        if not data:
            return 
        self.node_status = data["node_status"]
        self.mem_size_max = data["mem_size_max"]
        self.mem_size_available = data["mem_size_available"]
        self.disk_size_max = data["disk_size_max"]
        self.disk_size_available = data["disk_size_available"]
        self.number_cores_max = data["number_cores_max"]
        self.number_cores_available = data["number_cores_available"]

class NodeDetail:
    uri = ""
    vir_conn = None
    config_max_disk = 0
    config_max_mem = 0
    config_max_cores = 0
    disk_max = 0
    mem_max = 0
    cores_max = 0
    
    def __init__(self, data={}):
        if not data:
            return
        self.uri = data["uri"]
        #self.vir_conn = None
        self.config_max_disk = data["config_max_disk"]
        self.config_max_mem = data["config_max_mem"]
        self.config_max_cores = data["config_max_cores"]
        self.disk_max = data["disk_max"]
        self.mem_max = data["mem_max"]
        self.cores_max = data["cores_max"]

class Result:
    code = 0xFFFFFFFF
    msg = ""
    
    def __init__(self, data={}):
        if not data:
            return
        self.code = data["code"]
        self.msg = data["msg"]
        
    @staticmethod
    def new(code, msg):
        rs = Result()
        rs.code = code
        rs.msg = msg
        return rs

def meta_state_factory(clazz, array):
    setattr(clazz, '_map', {})
    setattr(clazz, "state_name", staticmethod(lambda x: clazz._map[x]))
    for (k, v) in array:
        setattr(clazz, k, v)
        clazz._map[v] = k
    
#meta_state_factory = lambda clazz, array: [setattr(clazz, k, v) for (k, v) in array]

class ControlState:
    RUNNING = 1
    LOST = 2
    
class NodeState(ControlState): pass
    
#class InstanceState:
#    NOSTATE = 0
#    RUNNING = 1
#    BLOCKED = 2
#    PAUSED = 3
#    SHUTDOWN = 4
#    SHUTOFF = 5
#    CRASHED = 6
#    BOOTING = 7
#    CANCELED = 8
#    BUNDLING_SHUTDOWN = 9
#    BUNDLING_SHUTOFF = 10
#    
#    PENDING = 11 # staging in data, starting to boot, failed to boot
#    EXTANT = 12 # guest OS booting, running, shutting down, cleaning up state
#    TEARDOWN = 13 # a marker for a terminated domain, one not taking up resources
    
class InstanceState: pass
instance_state_list = [("NOSTATE", 0),
                       ("RUNNING", 1),
                       ("BLOCKED", 2),
                       ("PAUSED", 3),
                       ("SHUTDOWN", 4),
                       ("SHUTOFF", 5),
                       ("CRASHED", 6),
                       ("BOOTING", 7),
                       ("CANCELED", 8),
                       ("BUNDLING_SHUTDOWN", 9),
                       ("BUNDLING_SHUTOFF", 10),
                       ("PENDING", 11), # staging in data, starting to boot, failed to boot
                       ("EXTANT", 12), # guest OS booting, running, shutting down, cleaning up state
                       ("TEARDOWN", 13)] # a marker for a terminated domain, one not taking up resources

# libvirt domain state enum
#enum virDomainState {
#VIR_DOMAIN_NOSTATE     =    0     : no state
#VIR_DOMAIN_RUNNING     =    1     : the domain is running
#VIR_DOMAIN_BLOCKED     =    2     : the domain is blocked on resource
#VIR_DOMAIN_PAUSED     =    3     : the domain is paused by user
#VIR_DOMAIN_SHUTDOWN     =    4     : the domain is being shut down
#VIR_DOMAIN_SHUTOFF     =    5     : the domain is shut off
#VIR_DOMAIN_CRASHED     =    6     : NB: this enum value will increase over ' as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.
#VIR_DOMAIN_LAST     =    7
#}

meta_state_factory(InstanceState, instance_state_list)

def main():
    print InstanceState.state_name(InstanceState.BOOTING)

if __name__ == '__main__':
    main()

