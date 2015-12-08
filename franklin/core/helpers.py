import hmac
import hashlib
import json
import logging
import os
import requests
import sys

from django.core.urlresolvers import reverse

from requests.exceptions import ConnectionError, HTTPError, Timeout
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework import status, permissions
from rest_framework.authentication import BaseAuthentication,\
                                          get_authorization_header
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.views import NAMESPACE
from social.apps.django_app.utils import load_backend, load_strategy

logger = logging.getLogger(__name__)


def make_rest_get_call(url, headers):
    response = None
    try:
        response = requests.get(url, headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST GET Connection exception : %s', e)
    except:
        logger.error('Unexpected REST GET error: %s', sys.exc_info()[0])

    if response is not None:
        if not status.is_success(response.status_code):
            logger.warn('Bad GET response code of %s', response.status_code)
    else:
        logger.error('GET response was None. This shouldn\'t happen')
        response = requests.Response()
        response.status_code = 500
    return response


def make_rest_post_call(url, headers, body):
    response = None
    try:
        response = requests.post(url, data=json.dumps(body), headers=headers)
    except (ConnectionError, HTTPError, Timeout) as e:
        logger.error('REST POST Connection exception : %s', e)
    except:
        logger.error('Unexpected REST POST error: %s', sys.exc_info()[0])

    if response is not None:
        if not status.is_success(response.status_code):
            logger.warn('Bad POST response code of %s', response.status_code)
    else:
        logger.error('POST response was None. This shouldn\'t happen')
        response = requests.Response()
        response.status_code = 500
    return response


def generate_ssh_keys():
    # TODO - use https://pypi.python.org/pypi/pycrypto here after 2.7 comes out
    return (None, None)


class GithubOnly(permissions.BasePermission):
    """ Security Check for certain API endpoints only called by Github."""

    def has_permission(self, request, view):
        secret = request.META.get("HTTP_X_HUB_SIGNATURE")
        if secret:
            # must convert to bytes for python 3.5 bug in hmac library
            key = bytes(os.environ['GITHUB_SECRET'].encode('ascii'))
            computed_secret = 'sha1=' + hmac.new(
                    key, request.body, hashlib.sha1).hexdigest()
            is_valid_github = hmac.compare_digest(computed_secret, secret)
            return is_valid_github
        return False


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
            strategy = load_strategy(request=request)
            path = NAMESPACE + ":complete"
            backend = 'github'
            backend = load_backend(strategy, backend,
                                   reverse(path, args=(backend,)))
            user = backend.do_auth(access_token=oauth_token)
            if not user:
                msg = 'Bad credentials'
                raise exceptions.AuthenticationFailed(msg)
            social = user.social_auth.get(provider='github')
            social.extra_data['access_token'] = oauth_token
            social.save()
        else:
            user = social_user.user
        return user, oauth_token
