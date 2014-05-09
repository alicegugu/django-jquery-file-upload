from django.conf.urls import patterns, include, url
from django.http import HttpResponseRedirect

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from class_based_auth_views.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'upload.views.home', name='home'),
    url(r'^$', LoginView.as_view(),name='login'),
    url(r'^indoor_tracking/', IndoorTrackingView.as_view()),
    url(r'^outdoor_tracking/', OutdoorTrackingView.as_view()),
    url(r'^wifiposition/',  WifiPositionView.as_view()),
    url(r'^indoorposition/', IndoorPositionView.as_view()),
    url(r'^gpsposition/', GPSPositionView.as_view()),
    url(r'^register/', RegisterView.as_view()),
    url(r'^contact_number/(?P<tag_id>\d{8})', ContactNumber.as_view(), name="12345678"),
	url(r'^on_or_off/(?P<tag_id>\d{8})/$' , On_or_Off.as_view()),
    #url(r'^$', lambda x: HttpResponseRedirect('/upload/new/')),
    url(r'^upload/', include('fileupload.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('userprofile.urls')),
    url(r'^logout/', LogoutView.as_view()),
)

import os
urlpatterns += patterns('',
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'media')}),
)
