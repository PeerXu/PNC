from django.contrib import admin
from clc.models import VirtualMachine, State, NetConfig, Volume, Instance, Socket, Node, Cluster, Cloud, Schedule, Config

#map(admin.site.register, [VirtualMachine, State, NetConfig, Volume, Instance, socket, Node, Cluster, Cloud])


admin.site.register(VirtualMachine)
admin.site.register(State)
admin.site.register(NetConfig)
admin.site.register(Socket)
admin.site.register(Volume)
admin.site.register(Instance)
admin.site.register(Node)
admin.site.register(Cluster)
admin.site.register(Cloud)
admin.site.register(Schedule)
admin.site.register(Config)
