import sys; sys.path.append('/opt/PNC'); del sys

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from clc.constant import STATE, CLOUD, CONFIG

from clc.models import Cloud, Cluster, Image, Kernel, Ramdisk, NetConfig, Instance, VirtualMachine, State

from common import utils
import config

def INSTANCE_INDEX(request):
    return render_to_response('instance/index.html',
                              context_instance=RequestContext(request, {'instances': Instance.objects.filter(user=request.user)}))

def IMAGE_INDEX(request):
    return render_to_response('image/index.html',
                              context_instance=RequestContext(request, {'images': Image.objects.all()}))

def view_hello(request):
    return render_to_response('hello_world.html')

def view_register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/clc")
    else:
        form = UserCreationForm()
    c = RequestContext(request, {
            'form': form
    })
    return render_to_response("user/register.html",context_instance=c)

def view_login(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect("/clc")
    return render_to_response("user/login.html",context_instance=RequestContext(request, {}))

def view_logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/clc")

def _mac_gen():
    import time, random, hashlib
    digest = (hashlib.md5(str(time.time())+str(random.randint(0,255)).zfill(3)).hexdigest()[random.randint(0,26):][:6]).upper()
    return config.INSTANCE_MAC_PREFIX + ':'.join([''] + reduce(lambda x, acc: (x[0][2:], x[1] + [x[0][:2]]), xrange(len(digest)/2), (digest, []))[1])

def view_remove_instance(request):
    try:
        inst_id = request.POST['name']
        inst = Instance.objects.get(instance_id=inst_id)
    except Exception, ex:
        print ex
        return INSTANCE_INDEX(request)

    inst.state = STATE['PENDING']
    inst.save()
    
#    print "remove instance image %s from %s" % (inst.image.image_id, inst.image.local_dev_real)
    utils.remove(inst.image.local_dev_real)
    image = inst.image
#    print "remove instance %s from database" % inst_id
    inst.delete()
#    print "remove instance image %s from database" % inst.image.image_id
    image.delete()
    return HttpResponseRedirect("/clc/instance")

def _image_copy_handler(src, dst, inst):
    import shutil
    try:
        shutil.copy(src, dst)
    finally:
        inst.image.state=STATE['ACTIVE']
        inst.image.save()
        inst.state=STATE['STOP']
        inst.save()

def view_add_instance(request):
    if request.method != "POST":
        return render_to_response('instance/add.html', context_instance=RequestContext(request, {}))

    inst_name = request.POST.get('name', '')
    if len(Instance.objects.filter(name=inst_name)) != 0:
        return render_to_response('instance/add.html', context_instance=RequestContext(request, {}))

    try:
        import threading

        user = User.objects.get(username=request.POST['username'])
        image = Image.objects.get(image_id=request.POST.get('image', ''))
        src = image.local_dev_real

        phy_name = image.local_dev.rsplit('.', 1)[0] + "-" + inst_name + ".img"
        Image.objects.create(image_id=image.image_id + "-" + inst_name,
                             remote_dev=image.remote_dev,
                             local_dev=phy_name,
                             local_dev_real=config.IMAGE_PATH+phy_name,
                             state=STATE['PENDING'])
        image = Image.objects.get(local_dev=phy_name)
        dst = image.local_dev_real

        params = VirtualMachine.objects.create(name='custom',
                                               cores=request.POST.get('cores', 1),
                                               mem=request.POST.get('memory', 64),
                                               disk=request.POST.get('disk', 0))

        Instance.objects.create(instance_id=inst_name,
                                name=inst_name,
                                image=image,
                                kernel=Kernel.objects.get(kernel_id='_'),
                                ramdisk=Ramdisk.objects.get(ramdisk_id='_'),
                                reservation_id="",
                                user=user,
                                params=params,
                                net=NetConfig.objects.create(ip="0.0.0.0",
                                                             mac=_mac_gen()),
                                state=STATE['PENDING'],)

        inst = Instance.objects.get(instance_id=inst_name)
        threading.Thread(target=_image_copy_handler, args=(src, dst, inst)).start()
        
    except Exception, ex:
        print ex
        params.delete()
        return render_to_response('instance/add.html',
                                  context_instance=RequestContext(request, {}))

    return HttpResponseRedirect("/clc/instance")


def view_detail_instance(request):

    if request.method != 'POST':
        return INSTANCE_INDEX(request)

    name = request.POST.get('name', None)
    if name == None:
        return INSTANCE_INDEX(request)
    
    try:
        inst = Instance.objects.get(instance_id=name)
    except Exception, ex:
        print ex
        return INSTANCE_INDEX(request)

    return render_to_response('instance/detail.html',
                              context_instance=RequestContext(request, {'instance': inst}))

def view_detail_image(request):
    if request.method != 'POST':
        return IMAGE_INDEX(request)

    id = request.POST.get('id', None)
    if id == None:
        return IMAGE_INDEX(request)

    try:
        img = Image.objects.get(image_id=id)
    except Exception, ex:
        print ex
        return IMAGE_INDEX(request)
    
    return render_to_response('image/detail.html',
                              context_instance=RequestContext(request, {'image': img}))

def view_edit_instance(request):

    if request.method != 'POST':
        return INSTANCE_INDEX(request)

    try:
        inst_id = request.POST['instance_id']
        cores = request.POST['cores']
        mem = request.POST['mem']
    except Exception, ex:
        print ex
        return INSTANCE_INDEX(request)

    try:
        inst = Instance.objects.get(instance_id=inst_id)
        if inst.state != STATE['STOP']: raise
    except Exception, ex:
        print ex
        return INSTANCE_INDEX(request)

    params = inst.params
    params.cores = cores
    params.mem = mem
    params.save()

    return INSTANCE_INDEX(request)

def view_instance(request):
    def start_handler(): return view_start_instance(request)
    def stop_handler(): return view_stop_instance(request)
    def detail_handler(): return view_detail_instance(request)
    def remove_handler(): return view_remove_instance(request)
    def edit_handler(): return view_edit_instance(request)

    if request.method == 'POST':
        option = request.POST.get('option', ['detail']).split()[0]
        return locals()[option + '_handler']()

    return INSTANCE_INDEX(request)

def view_image(request):
    def detail_handler(): return view_detail_image(request)
    
    if request.method == 'POST':
        option = request.POST.get('option', ['detail']).split()[0]
        return locals()[option + '_handler']()
    
    return IMAGE_INDEX(request)

def _schedule_instance(inst, nid=None):
    schedule = CONFIG().schedule.name
    schedule_name = '_schedule_instance_' + schedule
    try:
        _schedule_instance = globals()[schedule_name]
    except Exception, ex:
        print ex
        raise ex
    return _schedule_instance(inst.params, nid)

def _cluster_resource_point(cluster):
    return cluster.cores_max * config.CORES_POINT_PER_COUNT + cluster.mem_max * config.MEMORY_POINT_PER_MB + cluster.disk_max * config.DISK_POINT_PER_MB

def _verify_resource(params, cluster):
    lacks = []
    if cluster.cores_max < params.cores:
        lacks.append('cores')
    if cluster.mem_max < params.mem:
        lacks.append('memory')
    if cluster.disk_max < params.disk:
        lacks.append('disk')
    return lacks

def _schedule_instance_by_verify(verify):
    def warpper(params, _=None):
        point = 0
        perfect_res = None
        for cluster in Cluster.objects.filter(state=STATE['RUNNING']):
            if not _verify_resource(params, cluster):
                cur_point = _cluster_resource_point(cluster)
                if not perfect_res or verify(cur_point, point):
                    point = cur_point
                    perfect_res = cluster
        return perfect_res and perfect_res or None
    return warpper

def _schedule_instance_greed(params, _=None):
    _schedule_instance_greed = _schedule_instance_by_verify(lambda x, y: x<y)
    return _schedule_instance_greed(params, _)

def _schedule_instance_default(params, _=None):
    return _schedule_instance_greed(params)

def _schedule_instance_smart(params, _=None):
    _schedule_instance_smart = _schedule_instance_by_verify(lambda x, y: x>y)
    return _schedule_instance_smart(params, _)

def _schedule_instance_explicit(params, nid):
    return reduce(lambda x, xa: x and x or (reduce(lambda y, ya: y and y or (ya.name == nid and xa or None), xa.nodes.lal(), None)), Cluster.objects.filter(state=STATE['RUNNING']), None)

def view_start_instance(request):
    if request.method != "POST":
        return render_to_response('instance/index.html',
                                  context_instance=RequestContext(request, {}))
    args_dict = request.POST
    name = args_dict.get('name', None)
    if name == None:
        return render_to_response('instance/index.html',
                                  context_instance=RequestContext(request, {}))

    try:
        inst = Instance.objects.get(instance_id=name)
    except:
        return render_to_response('instance/index.html', 
                                  context_instance=RequestContext(request, {}))

    current_user = auth.get_user(request)
    if not inst.user.username == current_user.username:
        return render_to_response('instance/index.html', 
                                  context_instance=RequestContext(request, {}))

    # send start instance message to cc
    cc_name = _schedule_instance(inst)
    if cc_name == None:
        return render_to_response('instance/index.html',
                                  context_instance=RequestContext(request, {}))

    cc = Cluster.objects.get(name=cc_name)

    cc_server = utils.get_conctrller_object(utils.uri_generator(cc.socket.ip,
                                                                cc.socket.port))

    rs = cc_server.do_run_instances([inst.instance_id],
                                    None,
                                    inst.user_id,
                                    {'cores': inst.params.cores,
                                     'mem': inst.params.mem,
                                     'disk': inst.params.disk},
                                    inst.image.image_id, inst.image.local_dev_real,
                                    None, None,
                                    None, None,
                                    [inst.net.mac],
                                    None)

    if rs['code'] != 0:
        return render_to_response('instance/index.html',
                                  context_instance=RequestContext(request, {}))

    return HttpResponseRedirect("/clc/instance")

def view_stop_instance(request):

    if request.method != 'POST':
        return INSTANCE_INDEX(request)

    inst_id = request.POST.get('name', None)
    if inst_id == None:
        return INSTANCE_INDEX(request)

    try:
        inst = Instance.objects.get(instance_id=inst_id)
    except Exception, ex:
        return INSTANCE_INDEX(request)

    cc_server = None
    for cluster in Cluster.objects.all():
        if cc_server:
            break
        for node in cluster.nodes.all():
            if cc_server:
                break
            for inst_t in node.instances.all():
                if inst_t.instance_id == inst.instance_id:
                    cc_server = utils.get_conctrller_object(utils.uri_generator(cluster.socket.ip,
                                                                                cluster.socket.port))
                    break

    if cc_server is None:
        return INSTANCE_INDEX(request)
    
    try:
        rs = cc_server.do_terminate_instances([inst.instance_id])
        if rs['code'] != 0x0:
            return INSTANCE_INDEX(request)
    except Exception, ex:
        print ex
        return INSTANCE_INDEX(request)


    return HttpResponseRedirect("/clc/instance")

def view_add_image(request):
    if request.method != 'POST':
        return render_to_response('image/add.html', 
                                  context_instance=RequestContext(request, {}))

    try:
        name = request.POST['name']
        sys_type = request.POST['type']
        phy_name = request.POST['phyname']
        if not phy_name.endswith('.img'):
            raise Exception, 'error physics name'
    except Exception, ex:
        print ex
        return render_to_response('image/add.html', 
                                  context_instance=RequestContext(request, {}))

    img_id = 'img-%s-%s-%s' % (name, sys_type, phy_name[:-4])
    if len(Image.objects.filter(image_id=img_id)) != 0:
        return render_to_response('image/add.html', 
                                  context_instance=RequestContext(request, {}))

    Image.objects.create(image_id=img_id,
                         remote_dev='',
                         local_dev=phy_name,
                         local_dev_real=config.IMAGE_PATH+phy_name,
                         state=STATE['ACTIVE'])
    
    return HttpResponseRedirect("/clc")

def view_describe_cloud(request):
    return HttpResponseRedirect("/clc")

def view_describe_cluster(request, cid):
    return HttpResponseRedirect("/clc")

def view_describe_node(request, cid):
    return HttpResponseRedirect("/clc")

def view_describe_instance(request, iid):
    return HttpResponseRedirect("/clc")
