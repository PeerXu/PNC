import sys; sys.path.append('/opt/PNC'); del sys

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from clc.models import Image, Kernel, Ramdisk, NetConfig, Instance, VirtualMachine, State
import config

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

def view_add_instance(request):
    if request.method != "POST":
        return render_to_response('instance/add.html', context_instance=RequestContext(request, {}))

    inst_name = request.POST.get('name', '')
    if len(Instance.objects.filter(name=inst_name)) != 0:
        return render_to_response('instance/add.html', context_instance=RequestContext(request, {}))

    try:
        user = User.objects.get(username=request.POST['username'])
        image = Image.objects.get(image_id=request.POST.get('image', ''))
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
                                state=State.objects.get(name='stop'),)
    except Exception, ex:
        params.delete()
        return render_to_response('instance/add.html', context_instance=RequestContext(request, {}))

    return HttpResponseRedirect("/clc")

def view_add_image(request):
    if request.method != 'POST':
        return render_to_response('image/add.html', context_instance=RequestContext(request, {}))

    try:
        name = request.POST['name']
        sys_type = request.POST['type']
        phy_name = request.POST['phyname']
        if not phy_name.endswith('.img'):
            raise Exception, 'error physics name'
    except Exception, ex:
        print ex
        return render_to_response('image/add.html', context_instance=RequestContext(request, {}))

    img_id = 'img-%s-%s-%s' % (name, sys_type, phy_name[:-4])
    if len(Image.objects.filter(image_id=img_id)) != 0:
        return render_to_response('image/add.html', context_instance=RequestContext(request, {}))

    Image.objects.create(image_id=img_id,
                         remote_dev='',
                         local_dev=phy_name,
                         local_dev_real=config.IMAGE_PATH+phy_name,
                         state=State.objects.get(name='active'))
    
    return HttpResponseRedirect("/clc")
