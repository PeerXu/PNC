from django.core.management.base import BaseCommand, CommandError

from clc.models import Cluster, State, Socket


class Command(BaseCommand):
    ARG_LENGTH = 3
    
    def _usage(self):
        self.stdout.write("Usage: addcluster <cluster name> <ip> <port>\n")

    def handle(self, *args, **options):

        if len(args) != self.ARG_LENGTH:
            self._usage()
            return
        
        _types = [str, str, int]
        try:
            (name, ip, port) = map(lambda x: _types[x](args[x]), xrange(self.ARG_LENGTH))
        except ValueError:
            self._usage()
            return
        
        socket = Socket.objects.create(ip=ip, port=port)
        socket.save()
        state = State.objects.get(name='stop')
        Cluster.objects.create(name=name, socket=socket, state=state).save()
        
        self.stdout.write("add cluster: name=%s, ip=%s, port=%s\n" % (name, ip, port))
