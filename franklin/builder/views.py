import logging

from rest_framework.status import HTTP_200_OK
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Build, BranchBuild, Deploy, Environment, Site

logger = logging.getLogger(__name__)


class UpdateBuildStatus(APIView):
    permission_classes = (AllowAny,)

    def get_object(self, request, git_hash):
        try:
            received_env = request.data.get('environment', '')
            received_status = request.data.get('status', '')
            if received_status not in ['success', 'failed']:
                raise ParseError(detail="status must be 'success' or 'failed'")
            build = BranchBuild.objects.get(git_hash=git_hash)
            environment = Environment.objects.get(name__iexact=received_env,
                                                  site=build.site)
            return (environment, build)
        except (BranchBuild.DoesNotExist, Environment.DoesNotExist,
                Site.DoesNotExist) as e:
            raise NotFound(detail=e)

    def post(self, request, git_hash, format=None):
        environment, build = self.get_object(request, git_hash)
        received = request.data['status']
        build.status = Build.SUCCESS if received == 'success' else Build.FAILED
        build.save()
        if build.status == Build.SUCCESS:
            Deploy.objects.create(build=build, environment=environment)
        return Response(status=HTTP_200_OK)
