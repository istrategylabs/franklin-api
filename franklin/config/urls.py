"""franklin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from .views import health

from github.views import deploy_hook, RegisterRepo
from users.views import UserLogin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', UserLogin.as_view()),
    url(r'^login/$', UserLogin.as_view(), name='login'),
    url(r'^users/', include('users.urls', namespace='user')),
    url(r'^deployed/', deploy_hook, name='deploy'),
    url(r'^register/$', Register, name='register'),
    url(r'^unregister/$', unregister_repo, name='unregister'),
    url(r'^health/$', health, name='health'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('django.contrib.auth.urls', namespace='auth')),
]
