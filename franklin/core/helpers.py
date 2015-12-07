import hmac
import hashlib
import json
import logging
import os
import requests
import sys
from requests.exceptions import ConnectionError, HTTPError, Timeout

from rest_framework import status, permissions

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
