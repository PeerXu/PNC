from django.conf.urls import patterns, include, url
from clc import urls as clc_urls

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
FILE_PATH = os.path.dirname(__file__)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'PNC.views.home', name='home'),
    # url(r'^PNC/', include('PNC.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^css/(?P<path>.*)$', 'django.views.static.serve', 
     {'document_root': FILE_PATH + '/css'}),
    (r'^images/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': FILE_PATH + '/images'}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': FILE_PATH + '/js'}),
    (r'^clc/', include(clc_urls)),
)
