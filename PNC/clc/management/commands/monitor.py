import sys; sys.path.append('/opt/PNC/')
import time

from django.core.management.base import BaseCommand, CommandError

from clc.models import Cluster, Instance, State, Socket
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
            map(lambda x: server.do_add_node(x.name, x.socket.ip, x.socket.port), cluster.nodes.all())
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
        cluster.save()

        map(lambda x: self._refresh_node(*x), [(cluster, node) for node in cluster.nodes.all()])


    def _refresh_node(self, cluster, node):

        self.stdout.write('[INFO]: refresh node %s\n' % node.name)
        state = node.state.name
        cc_server = self._cluster_server(cluster)
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
            cc_server.do_add_node(node.name, node.socket.ip, node.socket.port)
            return

        res = ress[0]
        if res['node_status'] == 'ok':
            # refresh node detail
            node.config_max_cores = res['number_cores_available']
            node.config_max_mem = res['mem_size_available']
            node.config_max_disk = res['disk_size_available']
            node.cores_max = res['number_cores_max']
            node.mem_max = res['mem_size_max']
            node.disk_max = res['disk_size_max']
            node.save()
        else:
            try:
                cc_server.do_remove_node(node.name, True)
            except Exception, ex:
                print ex

        # update instance id to node
        rs = cc_server.do_describe_instances(None)
        insts = [ inst for inst in rs['data']['instances'] if inst['node']['id'] == node.name]

        for i in xrange(len(insts)):
            inst_dict = insts[i]
            inst_id = inst_dict['instance_id']
            try:
                inst_obj = Node.instances.get(instance_id=inst_id)
            except:
                inst_obj = Instance.objects.get(instance_id=inst_id)
                node.instances.add(inst_obj)

        map(lambda x: self._refresh_instance(cluster, node, x), node.instances.all())
        
    def _refresh_instance(self, cluster, node, inst):
        # to be continue
        cc_server = self._cluster_server(cluster)

        rs = cc_server.do_describe_instances([inst.instance_id])

        if rs['code'] != 0 or len(rs['data']['instances']) == 0:
            node.instances.remove(inst)
            node.save()
            self.stdout.write('[WARRING]: instance %s not found, remove it\n' % inst.instance_id)

        try:
            inst_data = rs['data']['instances'][0]
            (old_state, new_state) = (inst.state.name, State.objects.get(code=inst_data['state_code']))
            inst.state = new_state
            inst.net.ip = inst_data['net']['ip']
            inst.net.save()
        except Exception, ex:
            (old_state, new_state) = (inst.state.name, State.objects.get(name='stop'))
            inst.state = new_state
            self.stdout.write('[INFO]: remove instance %s from node %s\n' % (inst.instance_id, node.name))
            inst.net.ip == '0.0.0.0'
            inst.net.save()
            node.instances.remove(inst)
        inst.save()
        self.stdout.write('[INFO]: change instance %s state from %s to %s\n' % (inst.instance_id, old_state, new_state))

        self.stdout.write('[INFO]: refresh instance %s\n' % inst.instance_id)

        

    def handle(self, *args, **kwargs):
        while True:
            clusters = Cluster.objects.all()
            map(self._refresh_cluster, clusters)
            time.sleep(5)
