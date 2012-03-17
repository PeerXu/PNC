import sys; sys.path.append('/opt/PNC/')
import time

from django.core.management.base import BaseCommand, CommandError

from clc.models import Cluster, State, Socket
from common import utils


    

class Command(BaseCommand):
    def _cluster_server(self, cluster):
       return utils.get_conctrller_object(utils.uri_generator(cluster.socket.ip, cluster.socket.port)) 
    
    def _refresh_cluster(self, cluster):
        state = cluster.state.name
        fn = '_refresh_cluster_on_' + state
        
        if not hasattr(self, fn):
            self.stdout.write('[WARNNING]: UNKNOWN state: %s on cluster %s\n' % (state, cluster.name))
            return

        getattr(self, fn)(cluster)


    def _refresh_cluster_on_stop(self, cluster):
        self.stdout.write('[INFO]: refresh cluster %s on stop\n' % cluster.name)
        
        state = 'stop'

        # add node to cluster
        server = self._cluster_server(cluster)
        try:
            map(lambda x: server.do_add_node(*x), map(lambda x: (x.name, x.socket.ip, x.socket.port), cluster.nodes.all()))
        except:
            self.stdout.write('[WARNNING]: cluster %s not found\n' % cluster.name)
            return
        
        cluster.state = State.objects.get(name='running')
        cluster.save()
        self.stdout.write('[INFO]: modify cluster %s state from %s to %s\n' % (cluster.name, state, 'running'))


    def _refresh_cluster_on_running(self, cluster):
        self.stdout.write('[INFO]: refresh cluster %s on running\n' % cluster.name)

        server = self._cluster_server(cluster)

        try:
            rs = server.do_describe_resource()
            if rs['code'] != 0:
                raise
        except:
            stop_state = State.objects.get(name='stop')
            cluster.state = stop_state
            cluster.save()
            self.stdout.write('[WARNNING]: cannot connect cluster %s\n' % (cluster.name,))
            self.stdout.write('[INFO]: modify cluster %s state from %s to %s\n' % (cluster.name, 'running', 'stop'))
            return

        self.stdout.write(str(rs['data']['resource']) + '\n')


    def _refresh_node(self, node): pass
    def _refresh_instance(self, inst): pass

    def handle(self, *args, **kwargs):
        while True:
            clusters = Cluster.objects.all()
            map(self._refresh_cluster, clusters)
            time.sleep(5)
