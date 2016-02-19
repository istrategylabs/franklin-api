from django.conf.urls import url

from .views import health
from builder.views import UpdateBuildStatus
from github.views import deploy, deployable_repos, github_webhook, \
        repository_detail, repository_list, get_auth_token

urlpatterns = [
    url(r'^auth/github/$', get_auth_token, name='get_token'),
    url(r'^webhook/$', github_webhook, name='webhook'),

    # Registered Repo Operations
    url(r'^repos/$', repository_list, name='repo_list'),
    url(r'^repos/(?P<pk>[0-9]+)$', repository_detail, name='repo_details'),
    url(r'^repos/(?P<pk>[0-9]+)/deploy$', deploy, name='repo_deploy'),

    url(r'^repos/all/$', deployable_repos, name='deployable_repos'),
    url(r'^health/$', health, name='health'),
    url(r'^build/(?P<pk>\d+)/update/$', UpdateBuildStatus.as_view(),
        name='build'),
]
