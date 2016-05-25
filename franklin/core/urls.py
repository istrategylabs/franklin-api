from django.conf.urls import include, url

from .views import health
from builder.views import domain, UpdateBuildStatus
from github.views import builds, deployable_repos, github_webhook, \
    ProjectDetail, ProjectList, PromoteEnvironment, get_auth_token
from users.views import user_details


# /webhooks/
webhook_patterns = [
    url(r'^builder/builds/(?P<git_hash>[0-9a-zA-Z]+)$',
        UpdateBuildStatus.as_view(), name='builder'),
    url(r'^github/$', github_webhook, name='github'),
]


v1_patterns = [
    # Github Social Signin
    url(r'^auth/github/$', get_auth_token, name='get_token'),

    # Registered Repo Operations
    url(r'^projects/$', ProjectList.as_view(), name='project_list'),
    url(r'^projects/(?P<repo>[0-9]+)$', ProjectDetail.as_view(),
        name='project_details'),

    # Managing Builds endpoints
    url(r'^projects/(?P<repo>[0-9]+)/builds$', builds, name='project_builds'),

    # Build promotion
    url(r'^projects/(?P<repo>[0-9]+)/environments/(?P<env>[a-zA-Z]+)$',
        PromoteEnvironment.as_view(), name='promote_environment'),

    # User specific endpoints
    url(r'^user/$', user_details, name='user_details'),

    # Github passthrough endpoints
    url(r'^repos/$', deployable_repos, name='deployable_repos'),

    # Domain metadata
    url(r'^domains/$', domain, name='domain'),

    # Utilities
    url(r'^health/$', health, name='health'),
]

urlpatterns = [
    url(r'^v1/', include(v1_patterns)),

    # Webhooks
    url(r'^webhooks/', include(webhook_patterns, namespace='webhook')),
]
