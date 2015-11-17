import logging
import os
import yaml

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.helpers import make_rest_get_call, make_rest_post_call, GithubOnly 
from builder.models import Site
from builder.serializers import SiteSerializer
from .serializers import GithubWebhookSerializer

base_url = os.environ['API_BASE_URL']
github_base = 'https://api.github.com/'

logger = logging.getLogger(__name__)


def get_franklin_config(site, user):
    url = github_base + 'repos/' + site.owner.name + '/' + site.name + '/contents/.franklin.yml'
    #TODO - This will fetch the file from the default master branch
    #social = user.social_auth.get(provider='github')
    # token = social.extra_data['access_token']
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + os.environ['GITHUB_OAUTH'] 
              }
    config_metadata = make_rest_get_call(url, headers)

    if status.is_success(config_metadata.status_code):
        download_url = config_metadata.json().get('download_url', None)
        config_payload = make_rest_get_call(download_url, None)
        if status.is_success(config_payload.status_code):
            # TODO - validation and cleanup needed here similar to:
            # http://stackoverflow.com/a/22231372
            franklin_config = yaml.load(config_payload.text)
            return franklin_config
        else:
            return config_payload
    return config_metadata

def create_repo_webhook(site):
    # TODO - check for existing webhook and update if needed (or skip)
    
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + os.environ['GITHUB_OAUTH']
              }
    body = {
                'name': 'web',
                'events': ['push'],
                'active': True,
                'config': {
                                'url': base_url + 'deployed/',
                                'content_type': 'json',
                                'secret': os.environ['GITHUB_SECRET']
                          }
            }
    url = github_base + 'repos/' + site.owner.name + '/' + site.name + '/hooks'
    return make_rest_post_call(url, headers, body)

@api_view(['POST'])
def register_repo(request):
    """
    Setup a project to be deployed by franklin
    ---

    type:
        201:
            required: true
            type: string

    request_serializer: SiteSerializer
    omit_serializer: false

    parameters_strategy:
        form: merge
    parameters:
        - name: owner
          pytype: builder.serializers.OwnerSerializer
          required: true
    responseMessages:
        - code: 400
          message: Invalid json received or Bad Request from Github
        - code: 422
          message: Validation error from Github
    """
    # TODO - Lock this endpoint down so it's only callable from the future
    # admin panel.
    if request.method == 'POST':
        """
        # Calling github will look something like this
        user = User.objects.get(...)
        social = user.social_auth.get(provider='google-oauth2')
        response = requests.get(
                    'https://www.googleapis.com/plus/v1/people/me/people/visible',
                        params={'access_token':
                            social.extra_data['access_token']}
                        )
        friends = response.json()['items']
        """
        serializer = SiteSerializer(data=request.data)
        if serializer and serializer.is_valid():
            # TODO - Do this after we have the config instead?
            site = serializer.save()
            config = get_franklin_config(site, request.user)
            if config and not hasattr(config, 'status_code'):
                # Optional. Update DB with any relevant .franklin config
                pass
            response = create_repo_webhook(site)
            if not status.is_success(response.status_code):
                return Response(status=response.status_code)
            else:
                return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((GithubOnly, ))
def deploy_hook(request):
    """
    Private endpoint that should only be called from Github
    ---

    type:
        200:
            type: string
        201:
            type: string
        204:
            type: string

    request_serializer: GithubWebhookSerializer
    omit_serializer: false

    parameters_strategy:
        form: merge
    parameters:
        - name: head_commit
          pytype: github.serializers.HeadCommitSerializer
          required: true
        - name: repository
          pytype: github.serializers.RepositorySerializer
          required: true
    responseMessages:
        - code: 400
          message: Invalid json received or something else wrong.
    """
    if request.method == 'POST':
        event_type = request.META.get("HTTP_X_GITHUB_EVENT")
        if event_type:
            if event_type in ['push', 'create']:
                github_event = GithubWebhookSerializer(data=request.data)
                if github_event and github_event.is_valid():
                    site = github_event.get_existing_site()
                    if site:
                        environment = site.get_deployable_event(github_event)
                        if environment:
                            # This line helps with testing. We will remove once we add mocking.
                            if os.environ['ENV'] is not 'test':
                                environment.build()
                                return Response(status=status.HTTP_201_CREATED)
                        else:
                            # Likely a webhook we don't build for.
                            return Response(status=status.HTTP_200_OK)
                else:
                    logger.warning("Received an invalid Github Webhook message")
            elif event_type == 'ping':
                # TODO - update the DB with some important info here
                # repository{ 
                #           id, name, 
                #           owner{ id, login }, 
                #           sender{ id, login, site_admin }
                #           }
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            logger.warning("Received a malformed POST message")
    else:
        # Invalid methods are caught at a higher level
        pass
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_repos(request):
    if request.method == 'GET':
        return Response(request.user.details.get_user_repos())
