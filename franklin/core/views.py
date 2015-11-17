import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


@api_view(('GET',))
def health(request):
    return Response('Healthy!')
