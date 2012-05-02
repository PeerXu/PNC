from django.contrib.auth.models import User
from django.db import models

# Create your models here.

#class PathMapping(models.Model):
#    template_name = models.CharField(max_length=255)
#    current_path = models.CharField(max_length=255)
#    parent_mapping = models.ForeignKey(PathMapping, blank=True, null=True)
#    full_path = models.CharField(max_length=255, blank=True, null=True)
#    rebuild_flag = models.BooleanField() # not done

class VirtualMachine(models.Model):
    name = models.CharField(max_length=255)
    mem = models.IntegerField(max_length=255)
    cores = models.IntegerField(max_length=255)
    disk = models.IntegerField(max_length=255)
    
    def __unicode__(self):
        return self.name

class State(models.Model):
    code = models.IntegerField(max_length=255)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class NetConfig(models.Model):
    ip = models.CharField(max_length=255)
    mac = models.CharField(max_length=255)

    def __unicode__(self):
        return self.ip

class Volume(models.Model):
    volume_id = models.CharField(max_length=255, unique=True)
    remote_dev = models.CharField(max_length=255)
    local_dev = models.CharField(max_length=255)
    local_dev_real = models.CharField(max_length=255)
    state = models.ForeignKey(State)
    max_size = models.IntegerField(max_length=255)
    size = models.IntegerField(max_length=255)

    def __unicode__(self):
        return self.volume_id

class Image(models.Model):
    image_id = models.CharField(max_length=255, unique=True)
    remote_dev = models.CharField(max_length=255)
    local_dev = models.CharField(max_length=255)
    local_dev_real = models.CharField(max_length=255)
    state = models.ForeignKey(State)
    max_size = models.IntegerField(max_length=255)
    size = models.IntegerField(max_length=255)

    def __unicode__(self):
        return self.image_id

class Kernel(models.Model):
    kernel_id = models.CharField(max_length=255, unique=True)
    remote_dev = models.CharField(max_length=255)
    local_dev = models.CharField(max_length=255)
    local_dev_real = models.CharField(max_length=255)
    state = models.ForeignKey(State)
    max_size = models.IntegerField(max_length=255)
    size = models.IntegerField(max_length=255)

    def __unicode__(self):
        return self.kernel_id

class Ramdisk(models.Model):
    ramdisk_id = models.CharField(max_length=255, unique=True)
    remote_dev = models.CharField(max_length=255)
    local_dev = models.CharField(max_length=255)
    local_dev_real = models.CharField(max_length=255)
    state = models.ForeignKey(State)
    max_size = models.IntegerField(max_length=255)
    size = models.IntegerField(max_length=255)

    def __unicode__(self):
        return self.ramdisk_id


class Instance(models.Model):
    instance_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    image = models.ForeignKey(Image, null=True, blank=True)
    kernel = models.ForeignKey(Kernel, null=True, blank=True)
    ramdisk = models.ForeignKey(Ramdisk, null=True, blank=True)
    reservation_id = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User)
    state = models.ForeignKey(State)
    params = models.ForeignKey(VirtualMachine)
    net = models.ForeignKey(NetConfig)
    volumes = models.ManyToManyField(Volume, blank=True, null=True)

    def __unicode__(self):
        return self.instance_id

class Socket(models.Model):
    ip = models.CharField(max_length=255)
    port = models.IntegerField(max_length=255)

    def __unicode__(self):
        return "%s:%s" % (self.ip, self.port)

class Node(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    instances = models.ManyToManyField(Instance, blank=True, null=True)
    socket = models.ForeignKey(Socket)
    config_max_disk = models.IntegerField(max_length=255, default=0, editable=False)
    disk_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_mem = models.IntegerField(max_length=255, default=0, editable=False)
    mem_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_cores = models.IntegerField(max_length=255, default=0, editable=False)
    cores_max = models.IntegerField(max_length=255, default=0, editable=False)

    def __unicode__(self):
        return self.name

class Cluster(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    nodes = models.ManyToManyField(Node, blank=True, null=True)
    socket = models.ForeignKey(Socket)
    config_max_disk = models.IntegerField(max_length=255, default=0, editable=False)
    disk_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_mem = models.IntegerField(max_length=255, default=0, editable=False)
    mem_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_cores = models.IntegerField(max_length=255, default=0, editable=False)
    cores_max = models.IntegerField(max_length=255, default=0, editable=False)
    
    def __unicode__(self):
        return self.name

class Schedule(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    def __unicode__(self):
        return self.name

class Config(models.Model):
    name = models.CharField(max_length=255, unique=True)
    schedule = models.ForeignKey(Schedule)
    monitor_interval = models.IntegerField(max_length=255, default=3)

    def __unicode__(self):
        return self.name

class Cloud(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    config = models.ForeignKey(Config)
    clusters = models.ManyToManyField(Cluster, blank=True, null=True)
    terminated_instances = models.ManyToManyField(Instance, blank=True, null=True)
    config_max_disk = models.IntegerField(max_length=255, default=0, editable=False)
    disk_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_mem = models.IntegerField(max_length=255, default=0, editable=False)
    mem_max = models.IntegerField(max_length=255, default=0, editable=False)
    config_max_cores = models.IntegerField(max_length=255, default=0, editable=False)
    cores_max = models.IntegerField(max_length=255, default=0, editable=False)

    def __unicode__(self):
        return self.name
