from django.conf.urls import url

from .views import health
from builder.views import UpdateBuildStatus
from github.views import builds, deployable_repos, github_webhook, \
        ProjectDetail, ProjectList, promote_environment, get_auth_token

urlpatterns = [
    # Github Social Signin
    url(r'^auth/github/$', get_auth_token, name='get_token'),
    url(r'^webhook/$', github_webhook, name='webhook'),

    # Registered Repo Operations
    url(r'^projects/$', ProjectList.as_view(), name='project_list'),
    url(r'^projects/(?P<pk>[0-9]+)$',
        ProjectDetail.as_view(), name='project_details'),

    # Managing Builds endpoints
    url(r'^projects/(?P<pk>[0-9]+)/builds$', builds, name='project_builds'),

    # Github passthrough endpoints
    url(r'^repos/$', deployable_repos, name='deployable_repos'),

    # Build promotion
    url(r'repos/(?P<repo>[0-9]+)/environments/(?P<env>[a-zA-Z]+)/promote$',
        promote_environment, name='promote_environment'),

    # Private endpoints for Builder
    url(r'^build/(?P<pk>\d+)/update/$', UpdateBuildStatus.as_view(),
        name='build'),

    # Utilities
    url(r'^health/$', health, name='health'),
]
