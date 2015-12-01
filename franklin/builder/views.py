import logging
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics
from .models import Environment
# Create your views here.

from .serializers import EnvironmentStatusSerializer

logger = logging.getLogger(__name__)


class UpdateBuildStatus(generics.UpdateAPIView):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentStatusSerializer
    permission_classes = (AllowAny,)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({'message': 'status updated', }, status.HTTP_200_OK)
