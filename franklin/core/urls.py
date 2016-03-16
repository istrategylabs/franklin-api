from django.conf.urls import url

from .views import health
from builder.views import UpdateBuildStatus
from github.views import deploy, deployable_repos, github_webhook, \
        manage_environments, promote_environment, repository_detail, \
        repository_list, get_auth_token

urlpatterns = [
    # Github Social Signin
    url(r'^auth/github/$', get_auth_token, name='get_token'),
    url(r'^webhook/$', github_webhook, name='webhook'),

    # Registered Repo Operations
    url(r'^projects/$', repository_list, name='repo_list'),
    url(r'^repos/(?P<pk>[0-9]+)$', repository_detail, name='repo_details'),
    url(r'^repos/(?P<pk>[0-9]+)/deploy$', deploy, name='repo_deploy'),

    url(r'^repos/all/$', deployable_repos, name='deployable_repos'),

    # Environment management
    url(r'repos/(?P<repo>[0-9]+)/environments$', manage_environments,
        name='environments'),
    url(r'repos/(?P<repo>[0-9]+)/environments/(?P<env>[a-zA-Z]+)/promote$',
        promote_environment, name='promote_environment'),

    # Private endpoints for Builder
    url(r'^build/(?P<pk>\d+)/update/$', UpdateBuildStatus.as_view(),
        name='build'),

    # Utilities
    url(r'^health/$', health, name='health'),
]
