from clc.models import Cloud, Cluster, State, Instance

STATE = {}
map(lambda x: STATE.setdefault(x.name.upper(), x), State.objects.all())

CLOUD = lambda: Cloud.objects.get(name='default')
CLUSTER = lambda: Cluster.objects.all()
NODE = lambda: Node.objects.all()
CONFIG = lambda: CLOUD().config
INSTANCE = lambda: Instance.objects.all()
RUNNING_INSTANCE = lambda: [inst for inst in INSTANCE() if inst.state == STATE['RUNNING']]
