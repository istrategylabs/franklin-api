import logging
import os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.exceptions import ServiceUnavailable
from core.helpers import make_rest_get_call

logger = logging.getLogger(__name__)


def check_api_health(url):
    try:
        response = make_rest_get_call(url, '')
        if status.is_success(response.status_code):
            return response.json()
    except ServiceUnavailable:
        pass

    return {'status': 'unreachable'}


@api_view(('GET',))
@permission_classes((AllowAny, ))
def health(request):
    """
    For testing if the API is behaving properly
    """
    github_health_url = 'https://status.github.com/api/status.json'
    builder_health_url = os.environ['BUILDER_URL'] + '/health/'
    return Response({
        'api': {'status': 'good'},
        'github': check_api_health(github_health_url),
        'builder': check_api_health(builder_health_url)
    }, status=status.HTTP_200_OK)
