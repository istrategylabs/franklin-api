import logging
import os
import yaml
import requests

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.helpers import make_rest_get_call, make_rest_post_call, GithubOnly 
from builder.models import Site
from builder.serializers import SiteSerializer
from .serializers import GithubWebhookSerializer


github_secret = os.environ['SOCIAL_AUTH_GITHUB_SECRET']
base_url = os.environ['API_BASE_URL']
github_base = 'https://api.github.com/'

logger = logging.getLogger(__name__)


def get_franklin_config(site, user):
    url = github_base + 'repos/' + site.owner.name + '/' + site.name + '/contents/.franklin.yml'
    #TODO - This will fetch the file from the default master branch
    social = user.social_auth.get(provider='github')
    token = social.extra_data['access_token']
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + token 
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


def create_repo_webhook(site, user):
    # TODO - check for existing webhook and update if needed (or skip)
    social = user.social_auth.get(provider='github')
    token = social.extra_data['access_token']
    
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + token
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
        - code: 403
          message: Current user does not have deployment permissions
        - code: 422
          message: Validation error from Github
    """
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
            if request.user.details.has_repo_access(site):
                config = get_franklin_config(site, request.user)
                if config and not hasattr(config, 'status_code'):
                    # Optional. Update DB with any relevant .franklin config
                    pass
                response = create_repo_webhook(site, request.user)
                if not status.is_success(response.status_code):
                    return Response(status=response.status_code)
                else:
                    return Response(status=status.HTTP_201_CREATED)
            else:
                message = 'Current user does not have deployment permissions'
                logger.warn(message + ' | %s | %s', request.user, site)
                return Response(message, status=status.HTTP_403_FORBIDDEN)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def deployed_repos(request):
    """
    All repos currently deployed by Franklin that the user can manage.
    ---

    response_serializer: SiteSerializer

    responseMessages:
        - code: 500
          message: Error from Github.
    """
    if request.method == 'GET':
        if request.user.details.sites.count() == 0:
            github_repos = request.user.details.get_user_repos()
            # TODO - return error from github
            request.user.details.update_repos_for_user(github_repos)
        site_data = request.user.details.sites.all()
        serializer = SiteSerializer(site_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def deployable_repos(request):
    """
    All repos from Github that the user has the permission level to deploy
    ---

    responseMessages:
        - code: 500
          message: Error from Github.
    """
    if request.method == 'GET':
        # TODO - in the model, github response should map to a serializer which
        # we should use here to define the respone type
        github_repos = request.user.details.get_user_repos()
        # TODO - return error from github

        # While we are here, might as well update linkages between the user and
        # all active repos managed by Franklin
        request.user.details.update_repos_for_user(github_repos)
        return Response(github_repos, status=status.HTTP_200_OK)


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


def get_access_token(request):
    """
    Tries to get the access token from an OAuth Provider
    :param request:
    :param backend:
    :return:
    """
    url = 'https://github.com/login/oauth/access_token'
    secret = github_secret

    headers = {
        'content-type': 'application/json',
        'accept': 'application/json'
    }
    params = {
        "code": request.data.get('code'),
        "client_id": request.data.get('clientId'), 
        "redirect_uri": request.data.get('redirectUri'),
        "client_secret": secret
    }

    # Exchange authorization code for access token.
    r = make_rest_post_call(url, headers, params)
    if status.is_success(r.status_code):
        try:
            access_token = r.json().get('access_token', None) 
            response_data = Response({
                'token': access_token 
            }, status=status.HTTP_200_OK)
        except KeyError:
            response_data = Response({'status': 'Bad request',
                         'message': 'Authentication could not be performed with received data.'},
                        status=status.HTTP_400_BAD_REQUEST)
        return response_data
    else:
        return Response(status=r.status_code)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def get_auth_token(request):
    """
    View to authenticate with github using a client code
    ---
    """

    logger.info("Received token request from Dashboard")

    return get_access_token(request)
