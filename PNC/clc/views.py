from django.shortcuts import render_to_response

def view_hello(request):
    return render_to_response('hello_world.html')
    
