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

    def __unicode__(self):
        return self.volume_id

class Instance(models.Model):
    instance_id = models.CharField(max_length=255, unique=True)
    image_id = models.CharField(max_length=255, blank=True)
    image_url = models.CharField(max_length=255, blank=True)
    kernel_id = models.CharField(max_length=255, blank=True)
    kernel_url = models.CharField(max_length=255, blank=True)
    ramdisk_id = models.CharField(max_length=255, blank=True)
    ramdisk_url = models.CharField(max_length=255, blank=True)
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
    config_max_disk = models.IntegerField(max_length=255)
    disk_max = models.IntegerField(max_length=255)
    config_max_mem = models.IntegerField(max_length=255)
    mem_max = models.IntegerField(max_length=255)
    config_max_cores = models.IntegerField(max_length=255)
    cores_max = models.IntegerField(max_length=255)
    instances = models.ManyToManyField(Instance, blank=True, null=True)
    socket = models.ForeignKey(Socket)

    def __unicode__(self):
        return self.name

class Cluster(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    nodes = models.ManyToManyField(Node, blank=True, null=True)
    socket = models.ForeignKey(Socket)
    
    def __unicode__(self):
        return self.name

class Cloud(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    clusters = models.ManyToManyField(Cluster, blank=True, null=True)
    terminated_instances = models.ManyToManyField(Instance, blank=True, null=True)

    def __unicode__(self):
        return self.name
