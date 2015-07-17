from django.shortcuts import render
from django.http import HttpResponse

import requests

def auth(request):
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    session_code = request.args['code']

    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'code': session_code}
    headers = {'Accept': 'application/json'}

    r = requests.post('https://github.com/login/oauth/access_token',
                      json=payload, headers=headers)

    access_token = r.json()['access_token']
    return HttpResponse(status=200)
