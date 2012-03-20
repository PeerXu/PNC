from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from clc.models import Image, Kernel, Ramdisk, NetConfig, Instance, VirtualMachine, State


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
    return "ee:ee:ee:ee:ee:ee"

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

