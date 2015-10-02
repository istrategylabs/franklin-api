import logging
import os
import requests
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
    r = requests.get('https://api.github.com/user', params=payload)

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

def register_org():
    owner = os.environ['GITHUB_OWNER']
    oauth = os.environ['GITHUB_OAUTH']
    # Create an owner webhook to call a special registration endpoint anytime a
    # new repo is created.
    # POST /repos/:owner/:repo/hooks for 'repository' events. (see below)
    # Get existing repos and register them
    # GET /orgs/:org/repos from the github API
    # https://developer.github.com/v3/repos/#list-organization-repositories
    # For repo_in_response_json_array
    #   repo_name = repo.get('name', None)
    #   https://developer.github.com/v3/repos/contents/
    #   GET /repos/:owner/:repo/.franklin
    #   if response_is_200
    #       read_yaml_file
    #       with open(".franklin", 'r') as stream:
    #           franklin_config = yaml.load(stream)
    #       add repo to database (need to store several .travis config items)
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
