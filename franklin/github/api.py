import os
import yaml

from rest_framework import status
from rest_framework.response import Response

from core.helpers import make_rest_delete_call, make_rest_get_call, \
        make_rest_post_call, do_auth
from users.serializers import UserSerializer


def get_auth_header(user):
    social = user.social_auth.get(provider='github')
    token = social.extra_data['access_token']
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + token
              }
    return headers


def build_url(owner, repo, endpoint=''):
    base = 'https://api.github.com/repos'
    return '{0}/{1}/{2}/{3}'.format(base, owner, repo, endpoint)


def get_franklin_config(site, user):
    url = build_url(site.owner.name, site.name, 'contents/.franklin.yml')
    # TODO - This will fetch the file from the default master branch
    headers = get_auth_header(user)
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


def create_repo_deploy_key(site, user):
    # TODO - check for existing and update if needed (or skip)
    url = build_url(site.owner.name, site.name, 'keys')
    headers = get_auth_header(user)
    body = {
                'title': 'franklin readonly deploy key',
                'key': site.deploy_key,
                'read_only': True
            }
    return make_rest_post_call(url, headers, body)


def delete_deploy_key(site, user):
    if site.deploy_key_id:
        endpoint = 'keys/' + site.deploy_key_id
        url = build_url(site.owner.name, site.name, endpoint)
        headers = get_auth_header(user)
        return make_rest_delete_call(url, headers)
    return None


def create_repo_webhook(site, user):
    # TODO - check for existing webhook and update if needed (or skip)
    url = build_url(site.owner.name, site.name, 'hooks')
    headers = get_auth_header(user)
    body = {
                'name': 'web',
                'events': ['push'],
                'active': True,
                'config': {
                    'url': os.environ['API_BASE_URL'] + 'deployed/',
                    'content_type': 'json',
                    'secret': os.environ['GITHUB_SECRET']
                }
            }
    return make_rest_post_call(url, headers, body)


def delete_webhook(site, user):
    if site.webhook_id:
        endpoint = 'hooks/' + site.webhook_id
        url = build_url(site.owner.name, site.name, endpoint)
        headers = get_auth_header(user)
        return make_rest_delete_call(url, headers)
    return None


def get_access_token(request):
    """
    Tries to get the access token from an OAuth Provider
    """
    url = 'https://github.com/login/oauth/access_token'
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json'
    }
    params = {
        "code": request.data.get('code'),
        "client_id": request.data.get('clientId'),
        "redirect_uri": request.data.get('redirectUri'),
        "client_secret": os.environ['SOCIAL_AUTH_GITHUB_SECRET']
    }

    # Exchange authorization code for access token.
    r = make_rest_post_call(url, headers, params)
    if status.is_success(r.status_code):
        try:
            access_token = r.json().get('access_token', None)
            user = do_auth(access_token)
            serializer = UserSerializer(user)
            response_data = Response({
                'token': access_token,
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        except KeyError:
            response_data = Response({'status': 'Bad request',
                                      'message': 'Authentication could not be\
                                              performed with received data.'},
                                     status=status.HTTP_400_BAD_REQUEST)
        return response_data
    else:
        return Response(status=r.status_code)
