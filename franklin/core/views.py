import logging
import os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(('GET',))
@permission_classes((AllowAny, ))
def dashboard_init(request):
    """
    For the dashboard to initialize itself with the api
    ---
    type:
        client_id:
            type: string
            description: github client_id needed for social auth
            required: true
    """
    message = {'client_id': os.environ['SOCIAL_AUTH_GITHUB_KEY']}
    return Response(message, status=status.HTTP_200_OK)


@api_view(('GET',))
@permission_classes((AllowAny, ))
def health(request):
    """
    For testing if the API is behaving properly
    ---
    type:
        200:
            type: string
            description: All is well
            required: true
    """
    return Response(status=status.HTTP_200_OK)
