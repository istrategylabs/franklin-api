import logging
import os

from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, \
    HTTP_204_NO_CONTENT, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView
from rest_framework.response import Response

from .api import create_repo_deploy_key, create_repo_webhook, \
    delete_deploy_key, delete_webhook, get_access_token, get_all_repos, \
    get_repo
from .permissions import GithubOnly, UserHasProjectWritePermission
from .serializers import GithubWebhookSerializer, RepositorySerializer
from builder.models import Build, BranchBuild, Deploy, Environment, Site
from builder.serializers import BranchBuildSerializer, FlatSiteSerializer, \
    SiteSerializer
from core.exceptions import BadRequest, BadResource, ResourceExists, \
    ServiceUnavailable
from core.helpers import do_auth, validate_request_payload
from users.serializers import UserSerializer


logger = logging.getLogger(__name__)


class ProjectList(APIView):
    """
    Get all repos currently deployed by Franklin that the user can manage or
    register a new repo
    """
    permission_classes = (IsAuthenticated,
                          UserHasProjectWritePermission)

    def get(self, request, format=None):
        sites = request.user.details.get_user_repos()
        site_serializer = FlatSiteSerializer(sites, many=True)
        return Response(site_serializer.data, status=HTTP_200_OK)

    @validate_request_payload(['github', ])
    def post(self, request, format=None):
        project = request.data['github']
        owner, repo = project.split('/')
        if Site.objects.filter(name=repo, owner__name=owner).count() > 0:
            raise ResourceExists()

        # New project, call github for the details
        result = get_repo(owner, repo, request.user)
        serializer = RepositorySerializer(data=result.json())

        if serializer and serializer.is_valid():
            site = serializer.save()
            try:
                # Call Github to register a webhook
                webhook_r = create_repo_webhook(site, request.user)
                site.webhook_id = webhook_r.json().get('id', '')
                # Call Github to register a deploy key
                deploy_key_r = create_repo_deploy_key(site, request.user)
                site.deploy_key_id = deploy_key_r.json().get('id', '')
                site.save(user=request.user)
                site_serializer = SiteSerializer(
                    site, context={'user': request.user})
                return Response(site_serializer.data, status=HTTP_201_CREATED)
            except ServiceUnavailable:
                delete_site(site, request.user)
                raise
        raise BadRequest()


class ProjectDetail(APIView):
    """
    Rerieve or Delete a Github project with franklin
    """
    permission_classes = (IsAuthenticated,
                          UserHasProjectWritePermission)

    def get(self, request, repo, format=None):
        site = get_object_or_404(Site, github_id=repo)
        serializer = SiteSerializer(site, context={'user': request.user})
        return Response(serializer.data, status=HTTP_200_OK)

    def delete(self, request, repo, format=None):
        site = get_object_or_404(Site, github_id=repo)
        site.is_active = False
        site.save()
        return delete_site(site, request.user)


def delete_site(site, user):
    # TODO - This should be an async process that is thrown into a queue. The
    # site is no longer active, so the actual delete can occur lazily.
    try:
        delete_webhook(site, user)
        delete_deploy_key(site, user)
        site.delete()
        return Response(status=HTTP_204_NO_CONTENT)
    except:
        logger.warn('webhook/deploy_key delete failed | %s | %s', user, site)
        raise


@api_view(['GET'])
def deployable_repos(request):
    """
    All repos from Github that the user has the permission level to deploy
    """
    if request.method == 'GET':
        github_repos = get_all_repos(request.user)
        serializer = RepositorySerializer(github_repos, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


@api_view(['GET', 'POST'])
def builds(request, repo):
    """
    Deploy the tip of the default branch for the project
    or return all builds that exist for the project
    """
    site = get_object_or_404(Site, github_id=repo)

    if request.method == 'GET':
        builds = BranchBuild.objects.filter(site=site).all()
        serializer = BranchBuildSerializer(builds, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    elif request.method == 'POST':
        branch, git_hash = site.get_newest_commit(request.user)
        env = site.environments.filter(name='Staging').first()
        build = BranchBuild.objects.create(
            git_hash=git_hash, branch=branch, site=site)
        try:
            build.deploy(env)
        except ServiceUnavailable as e:
            serializer = BranchBuildSerializer(build)
            return Response({
                'detail': e.detail,
                'build': serializer.data
            }, status=HTTP_503_SERVICE_UNAVAILABLE)

        serializer = BranchBuildSerializer(build)
        return Response(serializer.data, status=HTTP_201_CREATED)


class PromoteEnvironment(APIView):
    """
    Promote a build to a higher environment
    """
    def get_object(self, request, repo, env):
        try:
            site = Site.objects.get(github_id=repo)
            environment = Environment.objects.get(name__iexact=env, site=site)
            uuid = request.data['uuid']
            build = BranchBuild.objects.get(uuid=uuid)
            return (environment, build)
        except (BranchBuild.DoesNotExist, Environment.DoesNotExist,
                Site.DoesNotExist) as e:
            raise NotFound(detail=e)

    @validate_request_payload(['uuid', ])
    def post(self, request, repo, env, format=None):
        environment, build = self.get_object(request, repo, env)
        current_deploy = environment.get_current_deploy()
        if current_deploy and build.id == current_deploy.id:
            raise ResourceExists(detail='already deployed')
        elif environment.name == 'Production':
            if build.status == Build.SUCCESS and build.environments.exists():
                Deploy.objects.create(build=build, environment=environment)
                return Response(status=HTTP_201_CREATED)
            raise BadResource(detail='build is not suitable for promotion')
        else:
            # Must be staging
            if build.status == Build.SUCCESS and build.environments.exists():
                Deploy.objects.create(build=build, environment=environment)
                return Response(status=HTTP_201_CREATED)
            elif build.status == Build.FAILED or build.status == Build.NEW:
                build.deploy(environment)
                return Response(status=HTTP_201_CREATED)
        raise BadRequest()


@api_view(['POST'])
@permission_classes((GithubOnly, ))
def github_webhook(request):
    """
    Private endpoint that should only be called from Github
    """
    if request.method == 'POST':
        event_type = request.META.get("HTTP_X_GITHUB_EVENT")
        if event_type:
            if event_type in ['push', 'create']:
                github_event = GithubWebhookSerializer(data=request.data)
                if github_event and github_event.is_valid():
                    github_event.create_build_and_deploy()
                    return Response(status=HTTP_201_CREATED)
                else:
                    logger.warning("Received invalid Github Webhook message")
                # Likely a webhook we don't build for.
                return Response(status=HTTP_200_OK)
            elif event_type == 'ping':
                # We COULD update the DB with some important info here
                # repository{ id, name, owner{ id, login },
                #             sender{ id, login, site_admin }}
                return Response(status=HTTP_204_NO_CONTENT)
        else:
            logger.warning("Received a malformed POST message")
    else:
        # Invalid methods are caught at a higher level
        pass
    raise BadRequest()


@api_view(['GET', 'POST'])
@permission_classes((AllowAny, ))
def get_auth_token(request):
    """
    View to authenticate with github using a client code
    """
    if request.method == 'GET':
        message = {'client_id': os.environ['SOCIAL_AUTH_GITHUB_KEY']}
        return Response(message, status=HTTP_200_OK)
    elif request.method == 'POST':
        response = get_access_token(request)
        try:
            access_token = response.json().get('access_token', None)
            user = do_auth(access_token)
            serializer = UserSerializer(user)
            response_data = Response({
                'token': access_token,
                'user': serializer.data
            }, status=HTTP_200_OK)
        except KeyError:
            raise BadRequest()
        return response_data
