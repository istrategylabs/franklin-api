import logging

from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable, try again later.'


class ResourceExists(APIException):
    status_code = 422
    default_detail = 'Resource already exists'


class BadResource(APIException):
    status_code = 422
    default_detail = 'Cannot perform that action with this resource'


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Problem parsing JSON'
