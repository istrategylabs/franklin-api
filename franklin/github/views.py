import logging
import os
import requests

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
