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
            rs = server.do_describe_resources()
            if rs['code'] != 0:
                raise
        except:
            self.stdout.write('[WARNNING]: cannot connect cluster %s\n' % (cluster.name,))
            cluster.state =State.objects.get(name='stop')
            cluster.save()
            self.stdout.write('[INFO]: modify cluster %s state from %s to %s\n' % (cluster.name, 'running', 'stop'))
            return

        res = rs['data']['resource']
        cluster.config_max_cores = res['number_cores_available']
        cluster.cores_max = res['number_cores_max']
        cluster.config_max_mem = res['mem_size_available']
        cluster.mem_max = res['mem_size_max']
        cluster.config_max_disk = res['disk_size_available']
        cluster.disk_max = res['disk_size_max']

#        self.stdout.write(str(rs['data']['resource']) + '\n')

        map(lambda x: self._refresh_node(*x), [(cluster, node) for node in cluster.nodes.all()])


    def _refresh_node(self, cluster, node):
        self.stdout.write('[INFO]: refresh node %s\n' % node.name)

        state = node.state.name

        cc_server = utils.get_conctrller_object(utils.uri_generator(cluster.socket.ip,
                                                                    cluster.socket.port))
        try:
            rs = cc_server.do_describe_node([node.name])
            if rs['code'] != 0:
                raise
        except:
            self.stdout.write('[WARNNING]: cluster %s not found\n' % cluster.name)
            node.state = State.objects.get(name='stop')
            node.save()
            self.stdout.write('[INFO]: modify node %s state from %s to %s\n' % (node.name, state, 'stop'))
            return

        ress = rs['data']['resources']
        
        if len(ress) == 0:
            self.stdout.write('[WARNNING]: node %s not found\n' % node.name)
            return

        res = ress[0]
        if res['node_status'] == 'ok':
#            import pdb; pdb.set_trace()
            # refresh node detail
            node.config_max_cores = res['number_cores_available']
            node.config_max_mem = res['mem_size_available']
            node.config_max_disk = res['disk_size_available']
            node.cores_max = res['number_cores_max']
            node.mem_max = res['mem_size_max']
            node.disk_max = res['disk_size_max']
            node.save()

        map(self._refresh_instance, node.instances.all())
        
    def _refresh_instance(self, inst):
        # to be continue
        self.stdout.write('[INFO]: refresh instance %s\n' % inst.instance_id)

    def handle(self, *args, **kwargs):
        while True:
            clusters = Cluster.objects.all()
            map(self._refresh_cluster, clusters)
            time.sleep(5)
