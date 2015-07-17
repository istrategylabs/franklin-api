import os

from django.shortcuts import render
from django.http import HttpResponse

import requests

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

def auth(request):
    context = {'client_id': client_id}
    return render(request, 'github/auth.html', context)

def callback(request):
    session_code = request.GET['code']

    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'code': session_code}
    headers = {'Accept': 'application/json'}

    r = requests.post('https://github.com/login/oauth/access_token',
                      json=payload, headers=headers)

    access_token = r.json()['access_token']
    return HttpResponse(status=200)
