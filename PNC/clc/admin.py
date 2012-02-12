from django.contrib import admin
from clc.models import VirtualMachine, NetConfig, Volume, Instance, Socket, Node, Cluster, Cloud

admin.site.register(VirtualMachine)
admin.site.register(NetConfig)
admin.site.register(Volume)
admin.site.register(Instance)
admin.site.register(Socket)
admin.site.register(Node)
admin.site.register(Cluster)
admin.site.register(Cloud)
