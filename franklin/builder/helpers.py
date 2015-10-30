import logging
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from rest_framework import status

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
    return response
