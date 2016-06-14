import logging

from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Build, BranchBuild, Deploy, Environment, Site
from .serializers import BuildSerializer
from core.exceptions import BadRequest

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def domain(request):
    """
    Returns details about a domain managed by Franklin
    """
    if request.method == 'GET':
        domain = request.GET.get('domain')
        if domain:
            environment = get_object_or_404(Environment, url=domain)
            serializer = BuildSerializer(environment.get_current_deploy())
            return Response(serializer.data, status=HTTP_200_OK)
    raise BadRequest()


class UpdateBuildStatus(APIView):
    permission_classes = (AllowAny,)

    def get_object(self, request, uuid):
        try:
            received_env = request.data.get('environment', '')
            received_status = request.data.get('status', '')
            if received_status not in ['success', 'failed']:
                raise ParseError(detail="status must be 'success' or 'failed'")
            build = BranchBuild.objects.get(uuid=uuid)
            environment = Environment.objects.get(name__iexact=received_env,
                                                  site=build.site)
            return (environment, build)
        except (BranchBuild.DoesNotExist, Environment.DoesNotExist,
                Site.DoesNotExist) as e:
            raise NotFound(detail=e)

    def post(self, request, uuid, format=None):
        environment, build = self.get_object(request, uuid)
        received = request.data['status']
        build.status = Build.SUCCESS if received == 'success' else Build.FAILED
        build.save()
        if build.status == Build.SUCCESS:
            Deploy.objects.create(build=build, environment=environment)
        return Response(status=HTTP_200_OK)
