import os

import requests

from django.shortcuts import render
from django.http import HttpResponse

from users.models import User


client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

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

def deploy_hook(request):
    pass
