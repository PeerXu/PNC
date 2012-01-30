#!/usr/bin/env python

#import commands
import StringIO
import threading
import re
#import time
#import random

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

def get_vale_from_outpout(output, key):
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
    kwargs['memory'] = memory
    kwargs['currentmemory'] = current_memory == -1 and memory or current_memory
    kwargs['vcpu'] = vcpu
    kwargs['disk_source_file'] = disk_path
    kwargs['disk_target_dev'] = "hd"
    kwargs['mac_address'] = mac

    return _gen_libvirt_xml(config.STANDARD_XML,  kwargs)

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
