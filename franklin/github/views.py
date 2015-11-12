import logging
import os
import yaml

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from builder.helpers import make_rest_get_call, make_rest_post_call, GithubOnly 
from builder.models import Site
from builder.serializers import SiteSerializer
from .serializers import GithubWebhookSerializer

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

base_url = os.environ['API_BASE_URL']
github_base = 'https://api.github.com/'

logger = logging.getLogger(__name__)

def auth(request):
    context = {'client_id': client_id}
    return render(request, 'github/auth.html', context)

"""
def callback(request):
    #Handles oauth callback from github and creates a new user
    #object with their Github username and newly obtained access_token
    
    session_code = request.GET['code']

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': session_code
    }

    headers = {'Accept': 'application/json'}

    r = requests.post(
        'https://github.com/login/oauth/access_token',
        json=payload,
        headers=headers
    )

    access_token = r.json()['access_token']

    payload = {'access_token': access_token}
    r = requests.get(github_base + 'user', params=payload)

    # Create user object once authenticated
    # TODO: Should probably check to see if user already exists
    User.objects.create(
        username=r.json()['login'],
        github_token=access_token
    )

    return HttpResponse(status=200)
"""

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
