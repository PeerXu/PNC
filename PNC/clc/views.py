from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext


def view_hello(request):
    return render_to_response('hello_world.html')

def view_register(request):
    if request.method == "POST":
#        import pdb; pdb.set_trace()
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/clc/demo/base")
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
        import pdb; pdb.set_trace()
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect("/clc/demo/base")
    return render_to_response("user/login.html",context_instance=RequestContext(request, {}))
