from django.conf.urls import include, url
from django.contrib import admin

from .views import ConvertTokenView, health
from github.views import deploy_hook, get_user_repos, register_repo

urlpatterns = [
    url(r'^deployed/$', deploy_hook, name='deploy'),
    url(r'^register/$', register_repo, name='register'),
    url(r'^userrepos/$', get_user_repos, name='userrepos'),
    url(r'^health/$', health, name='health'),
    url(r'^auth/convert-token/?$', ConvertTokenView.as_view(), name="convert_token"),
]
