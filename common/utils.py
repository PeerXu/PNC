#!/usr/bin/env python

import fcntl
import StringIO
import threading
import re
import time
import hashlib
import xmlrpclib
import os

import config
from common.lock import FileLock

kb2mb = lambda x: int(x) / 1024
b2mb = lambda x: int(x) / 1024 / 1024

def trans_by_unit(s):
    value, unit = s[:-1], s[-1]
    if unit == 'G':
        return int(float(value) * 1024)
    if unit == 'M':
        return int(value)

    raise Exception, "trans_by_unit error"

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
                return int(v)
            line = fo.readline()
        return 0
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
    kwargs['currentmemory'] = current_memory == -1 and kwargs['memory'] or current_memory * 1024
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

def uri_generator(ip, port):
    return "http://%s:%d" % (ip, port)

def get_conctrller_object(uri):
    return xmlrpclib.ServerProxy(uri, allow_none=True)
    
def remove(fn):
    os.path.exists(fn) and os.remove(fn)
    

class Lock():
    def __init__(self):
        self._lock = threading.Lock()
    def __enter__(self):
        self.acquire()
        return self
    def __exit__(self, *args):
        self.release()
    def acquire(self):
        self._lock.acquire()
    def release(self):
        self._lock.release()
    def locked(self):
        return self._lock.locked()

class DjangoLock():
    def __init__(self, filename):
        self.filename = filename
        self.handle = open(filename, 'w')
    def __del__(self):
        self.handle and self.handle.close()
    def __enter__(self):
        self.acquire()
        return self
    def __exit__(self):
        self.release()
    def acquire(self):
        fcntl.flock(self.filename, fcntl.LOCK_EX)
    def release(self):
        fcntl.flock(self.filename, fcntl.LOCK_UN)

class Semaphore():
    def __init__(self, max_sem=1):
        self._sem = threading.BoundedSemaphore(max_sem)
    def __enter__(self):
        self.acquire()
        return self
    def __exit__(self, *args):
        self.release()
    def acquire(self):
        self._sem.acquire()
    def release(self):
        self._sem.release()

class ResultThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.run_time = 0
        self.result = None
        self.is_done = False

    def run(self):
        now = time.time()
        self.result = self.func(*self.args, **self.kwargs)
        self.run_time = time.time() - now
        self.is_done = True

def _image_info_by_command(path):
    if not os.path.exists(path):
        return (-1, None)
    
    import commands
    (status, output) = commands.getstatusoutput('qemu-img info %s' % path)
    if status:
        return (status, None)

    try:
        m = {'image': ('image', lambda s: s), 
             'virtual_size': ('max_size', lambda x: b2mb(int(x.split('(', 1)[1].split()[0]))), 
             'disk_size': ('size', trans_by_unit)}
             
        d = {}
        map(lambda x: (lambda k, v: (lambda k1, v1: d.setdefault(m.get(k1, (k1,0))[0],m.get(k1, (k1, lambda s: s))[1](v1)))(k.replace(' ', '_'), v[1:]))(*x.split(':')), output.split('\n'))
    except:
        return (-1, None)
             
    return (0, d)

def image_info(path):
    try:
        ret, info = _image_info_by_command(path)
        if ret != 0:
            return {'image': path,
                    'max_size': 0,
                    'size': 0}
    except:
        return {'image': path,
                'max_size': 0,
                'size': 0}

    return info

def main():
    import sys; sys.path.append('/opt/PNC/')
    print image_info('/opt/PNC/images/1.img')
    
if __name__ == '__main__':
    main()
