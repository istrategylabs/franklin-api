from django.conf.urls import patterns, url

from .views import UserDashboard


urlpatterns = patterns('',
    url(r'^dashboard/$', UserDashboard.as_view(), name='dashboard'),
)
