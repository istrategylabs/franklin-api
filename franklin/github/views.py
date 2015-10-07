import logging
import os
import re
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import sys
import yaml

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from github.serializers import GithubWebhookSerializer
from users.models import User

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
owner = os.environ['GITHUB_OWNER']
oauth = os.environ['GITHUB_OAUTH']
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

# TODO - using the env vars, make a call to github and search all repos for
# .franklin files. If found, pull and register a webhook.
# Do we need to read the yml file now? Or is that something we do after a
# webhook event?

def make_rest_get_call(url, headers):
    response = None
    try:
        response = requests.get(url, headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST GET Connection exception : %s', e)
    except:
        logger.error('Unexpected REST GET error: %s', sys.exc_info()[0])

    if response is not None:
        if (response.status_code == requests.codes.ok):
            return response
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
        if (response.status_code == requests.codes.ok):
            return response
    return None

def create_owners_webhook():
    # TODO - Call github, create webhook if it doesn't exist.
    # We want to be called any time a new repo is created. This might also
    # serve as a way to find out if a .travis file has been added or changed in
    # any repo for the owner
    # POST /repos/:owner/:repo/hooks for 'repository' events. (see below)
    pass

def get_owners_repos():
    have_next_page = True
    url = github_base + 'orgs/' + owner + '/repos?per_page=100'
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + oauth
              }
    repos = []

    while have_next_page:
        response = None
        have_next_page = False # when in doubt, we'll leave the loop after 1
        response = make_rest_get_call(url, headers)

        if response is not None:
            # Add all of the repos to our list
            for repo in response.json():
                repo_data = {}
                repo_data['id'] = repo['id']
                repo_data['name'] = repo['name']
                repos.append(repo_data)

            # If the header has a paging link called 'next', update our url
            # and continue with the while loop
            if response.links and response.links.get('next', None):
                url = response.links['next']['url']
                have_next_page = True

    if not repos:
        logger.error('Failed to find repos for owner', owner)
    return repos

def get_franklin_config(repo_name):
    #   https://developer.github.com/v3/repos/contents/
    #   GET /repos/:owner/:repo/.franklin
    url = github_base + 'repos/' + owner + '/' + repo_name + '/contents/.franklin.yml'
    #TODO - This will fetch the file from the default master branch
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + oauth
              }
    response = make_rest_get_call(url, headers)

    if response is not None:
        print('Found .franklin for', repo_name)
        print('franklin_config', response)
        print('json', response.json())
        download_url = response.json().get('download_url', None)
        raw_data = make_rest_get_call(download_url, None)
        print('content is', raw_data.text)
    #       with open(".franklin", 'r') as stream:
        franklin_config = yaml.load(raw_data.text)
        print('config is', franklin_config)
        print('specific value is', franklin_config.get('hello', None))
    #           close?
    #           return franklin_config
    return None

def create_repo_webhook(config):
    #       https://developer.github.com/v3/repos/hooks/#create-a-hook
    #       POST /repos/:owner/:repo/hooks
    #       {
    #           name: 'web',
    #           config: {
    #                       "url": "our_api_url",
    #                       "content_type": "json"
    #                   },
    #           events: [push, create], # possibly don't need 'create'
    #           active: True
    #       }
    #       https://developer.github.com/webhooks/#events
    # TODO - check for existing webhook and update if needed (or skip)
    headers = {'content-type': 'application/json'}
    body = {
                'name': 'web',
                'events': ['push'],
                'active': True,
                'config': {
                                'url': 'TODO',
                                'content_type': 'json'
                          }
            }
    url = github_base + 'repos/' + owner + '/' + config.repo + '/hooks'
    response = make_rest_post_call(url, headers, body)
    if response:
        print('receive post response', response)
        pass
    else:
        #TODO - take action if creation failed?
        pass
    pass

@api_view(['GET'])
def register_org(request):
    if request.method == 'GET':
        # Create an owner webhook to call a special registration endpoint anytime a
        # new repo is created.
        # POST /repos/:owner/:repo/hooks for 'repository' events. (see below)
        create_owners_webhook()
        # Get existing repos and register them
        # GET /orgs/:org/repos from the github API
        repos = get_owners_repos()
        print('got repos', repos)
        # https://developer.github.com/v3/repos/#list-organization-repositories
        for repo in repos:
            repo_name = repo.get('name', None)
            # TODO - Temp debugging code
            if repo_name == 'ampm':
                config = get_franklin_config(repo_name)
                if config:
            #       add repo to database (need to store several .travis config items)
                    create_repo_webhook(config)
        return Response(repos)

@api_view(['POST'])
def deploy_hook(request):
    if request.method == 'POST':
        # Github webhooks contain special headers we can check for
        event_type = request.META.get("HTTP_X_GITHUB_EVENT")
        # Possibly useful for validation/security 
        # request.META.get("HTTP_X_GITHUB_DELIVERY")

        if event_type and event_type == "push":
            # For now, we only support push to branch events
            # TODO - We should also only support pushes to specific branches

            updated_site = GithubWebhookSerializer(data=request.data)
            if updated_site.is_valid():
                updated_site.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                logger.warning("Received an invalid Github Webhook message")
        else:
            logger.warning("Received a malformed POST message")
    else:
        # Invalid methods are caught at a higher level
        pass
    return Response(status=status.HTTP_400_BAD_REQUEST)
