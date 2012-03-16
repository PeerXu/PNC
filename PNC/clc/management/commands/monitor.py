from django.core.management.base import BaseCommand, CommandError

from clc.models import Cluster, Node, State, Socket

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("monitor process\n")

        
