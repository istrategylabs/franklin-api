import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from users.serializers import UserSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
def user_details(request):
    """ Returns details about the current user token passed in
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
