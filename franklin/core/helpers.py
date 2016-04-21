import json
import logging
import requests
import sys
from functools import wraps
from urllib.parse import urlparse

from django.core.urlresolvers import reverse
from django.utils.decorators import available_attrs

from Crypto.PublicKey import RSA
from requests.exceptions import ConnectionError, HTTPError, Timeout
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.authentication import BaseAuthentication,\
    get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.views import NAMESPACE
from social.apps.django_app.utils import load_backend, load_strategy

from .exceptions import BadRequest, ServiceUnavailable

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

    if response is None or status.is_server_error(response.status_code):
        msg = '{0} {1}'.format('Service temporarily unavailable:',
                               urlparse(url).netloc)
        raise ServiceUnavailable(detail=msg)
    elif status.is_client_error(response.status_code):
        raise BadRequest()
    elif status.is_redirect(response.status_code):
        logger.warn('Redirect %s for %s', response.status_code, url)

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
            raise AuthenticationFailed('Credentials are malformed')
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
        raise AuthenticationFailed(e.response.json())
    if not user:
        raise AuthenticationFailed('Bad credentials')
    social = user.social_auth.get(provider='github')
    social.extra_data['access_token'] = oauth_token
    social.save()
    return user


def validate_request_payload(payload_value_list):
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def _wrapped_view(self, request, *args, **kwargs):
            for key in payload_value_list:
                if key not in request.data:
                    raise BadRequest("request missing key '{}'".format(key))
            return func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator
