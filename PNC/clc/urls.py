from django.conf.urls import patterns
from django.views.generic.base import TemplateView
import os

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
    ('^instance/$', "clc.views.view_instance"),
    ('^instance/start', "clc.views.view_start_instance"),
    ('^instance/stop', "clc.views.view_stop_instance"),
    ('^instance/add', "clc.views.view_add_instance"),
    ('^instance/remove', "clc.views.view_remove_instance"),
    ('^instance/detail', "clc.views.view_detail_instance"),
    # IMAGE
    ('^image/$', 'clc.views.view_image'),
    ('^image/add', "clc.views.view_add_image"),
    # RESOURCE
#    ('^resource/(?P<object>.*)/(?P<id>.*)$', "clc.views.view_describe_resource"),
    ('^resource/cloud$', "clc.views.view_resource_cloud"),
)
