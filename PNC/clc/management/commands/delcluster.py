from django.core.management.base import BaseCommand, CommandError

from clc.models import Cluster, State, Socket


class Command(BaseCommand):
    ARG_LENGTH = 1
    
    def _usage(self):
        self.stdout.write("Usage: delcluster <cluster name>\n")

    def handle(self, *args, **options):

        if len(args) != self.ARG_LENGTH:
            self._usage()
            return
        
        _types = [str]
        try:
            (name,) = map(lambda x: _types[x](args[x]), xrange(self.ARG_LENGTH))
        except ValueError:
            self._usage()
            return

        try:
            cluster = Cluster.objects.get(name=name)
            cluster.delete()
        except:
            self.stdout.write("[WARNNING] cluster: " + name + " not found\n")
            return

        self.stdout.write("delete cluster: " + name + "\n")
