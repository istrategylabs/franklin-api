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

from builder.views import build_status

from github.views import auth, callback, deploy_hook

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/', auth, name='auth'),
    url(r'^callback/', callback, name='callback'),
    url(r'^deployed/', deploy_hook, name='deploy'),
    url(r'^health/$', health, name='health'),
    url(r'^status/$', build_status, name='status'),
]
