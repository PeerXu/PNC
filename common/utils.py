#!/usr/bin/env python

import StringIO
import threading
import re
import time
import hashlib

import config

kb2mb = lambda x: int(x) / 1024

#def get_sys_info(script_name="get_sys_info"):
#    script_cmd = config.TOOLS_PATH + script_name
#    (status, output) = commands.getstatusoutput(script_cmd)
#    if status:
#        return (0, 0)
#    
#    mem, cores = tuple([ int(x.split("=")[1]) for x in output.split("\n")])
#    return kb2mb(mem), cores

def get_value_from_outpout(output, key):
    if not isinstance(output, str):
        return -1 
    
    fo = None
    try:
        fo = StringIO.StringIO(output)
        line = fo.readline()
        while line:
            (k, v) = line.split("=")
            if k == key:
                return v
            line = fo.readline()
        return None
    finally:
        fo and fo.close()

def _gen_libvirt_xml(std_xml, arguments, std_fm="""{{ %s }}"""):
    def check_arguments():
        std_args = re.findall("{{ .* }}", std_xml)
        keys = arguments.keys()
        return reduce(lambda x, acc: std_fm % acc in std_args and x,
                      keys,
                      True)
    
    def format_arguments():
        rs = {}
        for (k, v) in arguments.items():
            rs.setdefault(k.upper(), v)
        return rs

    arguments = format_arguments()
    if not check_arguments():
        return None
    return reduce(lambda x, (k, v): x.replace(std_fm % k, str(v)), arguments.items(), std_xml)

def gen_libvirt_xml(name, uuid, memory, vcpu, disk_path, mac, current_memory=-1):
    kwargs = {}
    kwargs['name'] = name
    kwargs['uuid'] = uuid
    kwargs['memory'] = memory * 1024
    kwargs['currentmemory'] = current_memory == -1 and memory or current_memory * 1024
    kwargs['vcpu'] = vcpu
    kwargs['disk_source_file'] = disk_path
    kwargs['disk_target_dev'] = "hd"
    kwargs['mac_address'] = mac

    return _gen_libvirt_xml(config.STANDARD_XML,  kwargs)

def uuid_generator(slat):
    now = time.time()
    m = hashlib.new("md5", str(now))
    m.update(slat)
    tmp = m.hexdigest()
    return tmp[0:8] + "-" + tmp[8:12] + "-" + tmp[12:16] + "-" + tmp[16:20] + "-" + tmp[20:32]

def mac_generator(slat):
    now = time.time()
    m = hashlib.new("md5", str(now))
    m.update(slat)
    tmp = m.hexdigest()
    tmp = tmp[:6]
    return config.INSTANCE_MAC_PREFIX + ":" + str(tmp[0:2]) + ":" + str(tmp[2:4]) + ":" + str(tmp[4:6])
    

class Lock():
    #_rand = random.Random()
    def __init__(self):
        self._lock = threading.Lock()
        
    def acquire(self):
        #while self.locked(): time.sleep(self._rand.random())
        self._lock.acquire()
    def release(self):
        self._lock.release()
    def locked(self):
        return self._lock.locked()

        

def main():
    print gen_libvirt_xml("test",
                          "00-000-0000",
                          256,
                          1,
                          "/home/peer/image/xp.img",
                          "00:00:00:00:00:00")
    pass
    
if __name__ == '__main__':
    main()
