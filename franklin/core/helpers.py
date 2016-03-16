import json
import logging
import requests
import sys

from django.core.urlresolvers import reverse

from Crypto.PublicKey import RSA
from requests.exceptions import ConnectionError, HTTPError, Timeout
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework import status
from rest_framework.authentication import BaseAuthentication,\
                                          get_authorization_header
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.views import NAMESPACE
from social.apps.django_app.utils import load_backend, load_strategy

logger = logging.getLogger(__name__)


def make_rest_call(method, url, headers, data=None):
    response = None
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, data=data, headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST %s Connection exception : %s', method, e)
    except:
        logger.error('Unexpected REST %s error: %s', method, sys.exc_info()[0])

    if response is not None:
        if not status.is_success(response.status_code):
            logger.warn('Bad %s response code of %s',
                        method, response.status_code)
    else:
        logger.error('%s response was None. This shouldn\'t happen', method)
        response = requests.Response()
        response.status_code = 500
    return response


def make_rest_delete_call(url, headers):
    return make_rest_call('DELETE', url, headers)


def make_rest_get_call(url, headers):
    return make_rest_call('GET', url, headers)


def make_rest_post_call(url, headers, body):
    return make_rest_call('POST', url, headers, json.dumps(body))


def generate_ssh_keys():
    key = RSA.generate(2048)
    pubkey = key.publickey().exportKey('OpenSSH')
    return (pubkey.decode('UTF8'), key.exportKey('PEM').decode('UTF8'))


class SocialAuthentication(BaseAuthentication):
    """
    Used in DEFAULT_AUTHENTICATION_CLASSES settings for authentication.
    This setting allows users to authenticate with only a Github oauth token.
    """
    def authenticate(self, request):
        auth_header = get_authorization_header(request)\
                            .decode(HTTP_HEADER_ENCODING)
        auth = auth_header.split()
        if not auth or auth[0].lower() != 'bearer':
            return None
        if len(auth) == 1:
            msg = 'Credentials are malformed'
            raise exceptions.AuthenticationFailed(msg)
        oauth_token = auth[1]

        social_user = UserSocialAuth.objects\
                                    .filter(extra_data__contains=oauth_token)\
                                    .first()
        if not social_user:
            # User does not exist in our DB, attempt social auth
            user = do_auth(oauth_token)
        else:
            user = social_user.user
        return user, oauth_token


def do_auth(oauth_token):
    strategy = load_strategy()
    path = NAMESPACE + ":complete"
    backend = 'github'
    backend = load_backend(strategy, backend,
                           reverse(path, args=(backend,)))
    try:
        user = backend.do_auth(access_token=oauth_token)
    except requests.HTTPError as e:
        msg = e.response.json()
        raise exceptions.AuthenticationFailed(msg)
    if not user:
        msg = 'Bad credentials'
        raise exceptions.AuthenticationFailed(msg)
    social = user.social_auth.get(provider='github')
    social.extra_data['access_token'] = oauth_token
    social.save()
    return user
