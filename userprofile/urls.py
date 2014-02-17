from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^profile/$', 'userprofile.views.user_profile'),
	url(r'^api/alert/$','userprofile.views.alert_api'),
	url(r'^api/end/$', 'userprofile.views.end_api')
	)