from django.conf.urls import url

from .views import dashboard_init, health
from builder.views import UpdateBuildStatus
from github.views import deploy_hook, deployable_repos, repository_detail, \
        repository_list, get_auth_token

urlpatterns = [
    url(r'^auth/github/$', get_auth_token, name='get_token'),
    url(r'^dashboard/init/$', dashboard_init, name='dashboard_init'),
    url(r'^deployed/$', deploy_hook, name='deploy'),
    url(r'^repos/$', repository_list, name='repo_list'),
    url(r'^repos/(?P<pk>[0-9]+)$', repository_detail, name='repo_details'),
    url(r'^user/repos/deployable/$', deployable_repos,
        name='deployable_repos'),
    url(r'^health/$', health, name='health'),
    url(r'^build/(?P<pk>\d+)/update/$', UpdateBuildStatus.as_view(),
        name='build'),
]
