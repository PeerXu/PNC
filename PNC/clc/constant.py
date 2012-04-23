from clc.models import Cloud, Cluster, State

STATE = {}
map(lambda x: STATE.setdefault(x.name.upper(), x), State.objects.all())

CLOUD = lambda: Cloud.objects.get(name='default')
CLUSTER = lambda: Cluster.objects.all()
NODE = lambda: Node.objects.all()
CONFIG = lambda: CLOUD().config
