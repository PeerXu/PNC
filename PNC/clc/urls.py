from django.conf.urls import patterns
from django.views.generic.base import TemplateView
import os
#import pdb; pdb.set_trace()

FILE_PATH = os.path.dirname(__file__)

urlpatterns = patterns('',
    ('^css/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': FILE_PATH + '/css'}),
    (r'^images/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': FILE_PATH + '/images'}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': FILE_PATH + '/js'}),
    ('^$', TemplateView.as_view(template_name='base.html')),
    ('^register$', "clc.views.view_register"),
    ('^login$', "clc.views.view_login"),
    ('^logout$', "clc.views.view_logout"),
    ('^demo/hello', "clc.views.view_hello"),
    # INSTANCE
    ('^instance/add', "clc.views.view_add_instance"),
    # IMAGE
    ('^image$', 'clc.views.view_image'),
    ('^image/add', "clc.views.view_add_image"),
#    ('^demo/base', TemplateView.as_view(template_name='base.html')),
)
