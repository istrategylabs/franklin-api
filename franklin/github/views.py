import json
import logging
import os
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import sys
import yaml

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from builder.models import Site
from github.serializers import GithubWebhookSerializer
from users.models import User

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

base_url = os.environ['API_BASE_URL']
github_base = 'https://api.github.com/'

logger = logging.getLogger(__name__)

def auth(request):
    context = {'client_id': client_id}
    return render(request, 'github/auth.html', context)

def callback(request):
    """ Handles oauth callback from github and creates a new user
    object with their Github username and newly obtained access_token
    """
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

def make_rest_get_call(url, headers):
    response = None
    try:
        response = requests.get(url, headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST GET Connection exception : %s', e)
    except:
        logger.error('Unexpected REST GET error: %s', sys.exc_info()[0])

    if response is not None:
        if status.is_success(response.status_code):
            return response
        else:
            logger.warn('Bad GET response code of', response.status_code)
    return None

def make_rest_post_call(url, headers, body):
    response = None
    try:
        response = requests.post(url, data=json.dumps(body), headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST POST Connection exception : %s', e)
    except:
        logger.error('Unexpected REST POST error: %s', sys.exc_info()[0])

    if response is not None:
        if status.is_success(response.status_code):
            return response
        else:
            logger.warn('Bad POST response code of', response.status_code)
    return None

# Not currently used. but it works.
#def get_owners_repos(owner_name):
#    have_next_page = True
#    url = github_base + 'orgs/' + owner_name + '/repos?per_page=100'
#    # TODO - Confirm that a header token is the best/most secure way to go
#    headers = {
#                'content-type': 'application/json',
#                'Authorization': 'token ' + oauth
#              }
#    repos = []
#
#    while have_next_page:
#        response = None
#        have_next_page = False # when in doubt, we'll leave the loop after 1
#        response = make_rest_get_call(url, headers)
#
#        if response is not None:
#            # Add all of the repos to our list
#            for repo in response.json():
#                repo_data = {}
#                repo_data['id'] = repo['id']
#                repo_data['name'] = repo['name']
#                repos.append(repo_data)
#
#            # If the header has a paging link called 'next', update our url
#            # and continue with the while loop
#            if response.links and response.links.get('next', None):
#                url = response.links['next']['url']
#                have_next_page = True
#
#    if not repos:
#        logger.error('Failed to find repos for owner', owner_name)
#    return repos

def get_site_from_request(request):
    owner_name = request.data.get('owner', None)
    owner_id = request.data.get('owner_id', None)
    repo_name = request.data.get('repository', None)
    repo_id = request.data.get('repository_id', None)
    if owner_id and repo_id:
        site, created = Site.objects.get_or_create(owner_id=owner_id, 
                                                   repo_name_id=repo_id)
        if site:
            site.owner = owner_name
            site.repo_name = repo_name
            site.oauth_token = os.environ['GITHUB_OAUTH']
            site.save()
            return site
    return None


def get_franklin_config(site):
    url = github_base + 'repos/' + site.owner + '/' + site.repo_name + '/contents/.franklin.yml'
    #TODO - This will fetch the file from the default master branch
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + site.oauth_token
              }
    response = make_rest_get_call(url, headers)

    if response is not None:
        download_url = response.json().get('download_url', None)
        raw_data = make_rest_get_call(download_url, None)
        # TODO - validation and cleanup needed here similar to:
        # http://stackoverflow.com/a/22231372
        franklin_config = yaml.load(raw_data.text)
        return franklin_config
    return None

def create_repo_webhook(site):
    # TODO - check for existing webhook and update if needed (or skip)
    
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + site.oauth_token
              }
    body = {
                'name': 'web',
                'events': ['push'],
                'active': True,
                'config': {
                                'url': base_url + 'deployed/',
                                'content_type': 'json'
                          }
            }
    url = github_base + 'repos/' + site.owner + '/' + site.repo_name + '/hooks'
    response = make_rest_post_call(url, headers, body)
    if response:
        return True
    return False

@api_view(['POST'])
def register_repo(request):
    # TODO - Lock this endpoint down so it's only callable from the future
    # admin panel.
    if request.method == 'POST':
        site = get_site_from_request(request)
        if site:
            config = get_franklin_config(site)
            if config:
                # update DB with any relevant .franklin config itmes here.

                # TODO - We should return the error we get from github if we
                # fail. Refactor this.
                success = create_repo_webhook(site)
                if not success:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_201_CREATED)

@api_view(['POST'])
def deploy_hook(request):
    if request.method == 'POST':
        # Github webhooks contain special headers we can check for
        event_type = request.META.get("HTTP_X_GITHUB_EVENT")
        # Possibly useful for validation/security 
        # request.META.get("HTTP_X_GITHUB_DELIVERY")

        if event_type:
            if event_type == 'push':
                # For now, we only support push to branch events
                # TODO - We should also only support pushes to specific branches

                github_event = GithubWebhookSerializer(data=request.data)
                if github_event:
                    site = github_event.get_existing_site()
                    if site and site.is_deployable_event(github_event):
                        site.save()
                        # This line helps with testing. We will remove once we add mocking.
                        if os.environ['ENV'] is not 'test':
                            site.build()
                            return Response(status=status.HTTP_201_CREATED)
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
