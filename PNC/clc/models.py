from django.db import models

# Create your models here.

#class PathMapping(models.Model):
#    template_name = models.CharField(max_length=255)
#    current_path = models.CharField(max_length=255)
#    parent_mapping = models.ForeignKey(PathMapping, blank=True, null=True)
#    full_path = models.CharField(max_length=255, blank=True, null=True)
#    rebuild_flag = models.BooleanField() # not done

class VirtualMachine(models.Model):
    mem = models.IntegerField(max_length=255)
    cores = models.IntegerField(max_length=255)
    disk = models.IntegerField(max_length=255)

class State(models.Model):
    code = models.IntegerField(max_length=255)
    name = models.CharField(max_length=255)

class NetConfig(models.Model):
    ip = models.CharField(max_length=255)
    mac = models.CharField(max_length=255)

class Volume(models.Model):
    volume_id = models.CharField(max_length=255, unique=True)
    remote_dev = models.CharField(max_length=255)
    local_dev = models.CharField(max_length=255)
    local_dev_real = models.CharField(max_length=255)
    state_code = models.IntegerField(max_length=255)

class Instance(models.Model):
    instance_id = models.CharField(max_length=255, unique=True)
    image_id = models.CharField(max_length=255)
    image_url = models.CharField(max_length=255)
    kernel_id = models.CharField(max_length=255)
    kernel_url = models.CharField(max_length=255)
    ramdisk_id = models.CharField(max_length=255)
    ramdisk_url = models.CharField(max_length=255)
    reservation_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    state = models.ForeignKey(State)
    params = models.ForeignKey(VirtualMachine)
    net = models.ForeignKey(NetConfig)
    volumes = models.ManyToManyField(Volume)

class Socket(models.Model):
    ip = models.CharField(max_length=255)
    port = models.IntegerField(max_length=255)

class Node(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    config_max_disk = models.IntegerField(max_length=255)
    disk_max = models.IntegerField(max_length=255)
    config_max_mem = models.IntegerField(max_length=255)
    mem_max = models.IntegerField(max_length=255)
    config_max_cores = models.IntegerField(max_length=255)
    cores_max = models.IntegerField(max_length=255)
    instances = models.ManyToManyField(Instance)
    socket = models.ForeignKey(Socket)

class Cluster(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    nodes = models.ManyToManyField(Node)
    socket = models.ForeignKey(Socket)

class Cloud(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State)
    clusters = models.ForeignKey(Cluster)
    terminated_instances = models.ManyToManyField(Instance)
