
#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Metadata:
    
    def __init__(self, data={}):
        if not data:
            self.correlation_id = ""
            self.user_id = ""
            return
        self.correlation_id = data["correlation_id"]
        self.user_id = data["user_id"]

class VirtualMachine:
    
    def __init__(self, data={}):
        
        if not data:
            self.mem = 0
            self.cores = 0
            self.disk = 0
            #self.dev_mapping = None
            return
        self.mem = data["mem"]
        self.cores = data["cores"]
        self.disk = data["disk"]
    
class NetConfig:
    
    def __init__(self, data={}):
        if not data:
            self.ip = "0.0.0.0"
            self.mac = "00:00:00:00:00:00"
            return 
        self.ip = data["ip"]
        self.mac = data["mac"]
    
    @staticmethod
    def new_instance(ip=None, mac=None):
        net = NetConfig()
        net.ip = ip and net.ip or '0.0.0.0'
        net.mac = mac and net.mac or '00:00:00:00:00:00'
        return net

class Volume:
    
    def __init__(self, data={}):
        if not data:
            self.volume_id = ""
            self.remote_dev = ""
            self.local_dev = ""
            self.local_dev_real = ""
            self.state_code = 0
            
        self.volume_id = data["volume_id"]
        self.remote_dev = data["remote_dev"]
        self.local_dev = data["local_dev"]
        self.local_dev_real = data["local_dev_real"]
        self.state_code = data["state_code"]

class Instance:
    
    def __init__(self, data={}):
        if not data:
            self.instance_id = ""
            self.image_id = ""
            self.image_url = ""
            self.kernel_id = ""
            self.kernel_url = ""
            self.ramdisk_id = ""
            self.ramdisk_url = ""
            self.reservation_id = ""
            self.user_id = ""
            self.state_code = 0 # RunInstance request arrival
            self.launch_time = 0 # STAGING -> BOOTING transition
            self.termination_time = 0 # when resources are release (-> TRERDOWN transtion)
            self.boot_time = 0
            self.params = None # value of VirtualMachine
            self.net = None # value of NetConfig
            self.volumes = [] # value of Volume
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

class ClusterInstance(Instance):
    def __init__(self, data={}):
        if not data:
            self.node = None # ClusterResource
            return
        Instance.__init__(self, data)

    @staticmethod
    def new_instance(instance_id,
                     reservation_id,
                     params,
                     image_id, image_url,
                     kernel_id, kernel_url,
                     ramdisk_id, ramdisk_url,
                     state,
                     net_config,
                     user_id,
                     node):
        inst = ClusterInstance()

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
        inst.node = node

        return inst

    
        
class NodeResource:
    
    def __init__(self, data={}):
        if not data:
            self.node_status = ""
            self.mem_size_max = 0
            self.mem_size_available = 0
            self.disk_size_max = 0
            self.disk_size_available = 0
            self.number_cores_max = 0
            self.number_cores_available = 0
            return
         
        self.node_status = data["node_status"]
        self.mem_size_max = data["mem_size_max"]
        self.mem_size_available = data["mem_size_available"]
        self.disk_size_max = data["disk_size_max"]
        self.disk_size_available = data["disk_size_available"]
        self.number_cores_max = data["number_cores_max"]
        self.number_cores_available = data["number_cores_available"]
        
    @staticmethod
    def new_instance(node_status,
                     mem_size_max,
                     mem_size_available,
                     disk_size_max,
                     disk_size_available,
                     number_cores_max,
                     number_cores_available):
        
        res = NodeResource()
        
        res.node_status = node_status
        res.mem_size_max = mem_size_max
        res.mem_size_available = mem_size_available
        res.disk_size_max = disk_size_max
        res.disk_size_available = disk_size_available
        res.number_cores_max = number_cores_max
        res.number_cores_available = number_cores_available
        
        return res

class ClusterResource(NodeResource):
    
    def __init__(self, data={}):
        if not data:
            self.uri = ""
            self.id = ""
            return
        
        NodeResource.__init__(self, data['resource'])
        self.uri = data['uri']
        self.id = data['id']
 
    @staticmethod
    def new_instance(node_status,
                     mem_size_max,
                     mem_size_available,
                     disk_size_max,
                     disk_size_available,
                     number_cores_max,
                     number_cores_available,
                     uri,
                     id):
        res = ClusterResource()

        res.node_status = node_status
        res.mem_size_max = mem_size_max
        res.mem_size_available = mem_size_available
        res.disk_size_max = disk_size_max
        res.disk_size_available = disk_size_available
        res.number_cores_max = number_cores_max
        res.number_cores_available = number_cores_available
        res.uri = uri
        res.id = id

        return res

class NodeDetail:
    
    def __init__(self, data={}):
        if not data:
            self.uri = ""
            self.vir_conn = None
            self.config_max_disk = 0
            self.config_max_mem = 0
            self.config_max_cores = 0
            self.disk_max = 0
            self.mem_max = 0
            self.cores_max = 0
            return
        
        self.uri = data["uri"]
        #self.vir_conn = None
        self.config_max_disk = data["config_max_disk"]
        self.config_max_mem = data["config_max_mem"]
        self.config_max_cores = data["config_max_cores"]
        self.disk_max = data["disk_max"]
        self.mem_max = data["mem_max"]
        self.cores_max = data["cores_max"]

class ClusterDetail:
    
    def __init__(self, data={}):
        if not data:
            self.uri = ""
            self.sched_policy = "DEFAULT"
            self.sched_state = 0
            self.config_max_disk = 0
            self.config_max_mem = 0
            self.config_max_cores = 0
            self.disk_max = 0
            self.mem_max = 0
            self.cores_max = 0
            return
        
        sched_policy = data['sched_policy']
        sched_state = data['sched_state']
        config_max_disk = data['config_max_disk']
        config_max_mem = data['config_max_mem']
        config_max_cores = data['config_max_cores']
        disk_max = data['disk_max']
        mem_max = data['mem_max']
        cores_max = data['cores_max']
    
    @staticmethod
    def new_instance(sched_policy,
                     sched_state,
                     config_max_disk,
                     config_max_mem,
                     config_max_cores,
                     disk_max,
                     mem_max,
                     cores_max):
        cd = ClusterDetail()

        cd.sched_policy = sched_policy
        cd.sched_state = sched_state
        cd.config_max_disk = config_max_disk
        cd.config_max_mem = config_max_mem
        cd.config_max_cores = config_max_cores
        cd.disk_max = disk_max
        cd.mem_max = mem_max
        cd.cores_max = cores_max

        return cd
    
class Result:
    
    def __init__(self, data={}):
        if not data:
            self.code = 0xFFFF
            self.data = None
            return
        
        self.code = data["code"]
        self.data = data["data"]
        
    @staticmethod
    def new(code, data):
        rs = Result()
        rs.code = code
        rs.data = data
        return rs

def meta_state_factory(clazz, array):
    setattr(clazz, '_map', {})
    setattr(clazz, "state_name", staticmethod(lambda x: clazz._map[x]))
    for (k, v) in array:
        setattr(clazz, k, v)
        clazz._map[v] = k
    
class ControlState:
    RUNNING = 1
    LOST = 2
    
class NodeState(ControlState): pass

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
