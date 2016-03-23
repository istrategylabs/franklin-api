import logging
import os
import sys

from django.http import Http404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from .api import create_repo_deploy_key, create_repo_webhook, \
    delete_deploy_key, delete_webhook, get_access_token, get_all_repos, \
    get_repo
from .permissions import GithubOnly, UserIsProjectAdmin
from .serializers import GithubWebhookSerializer, RepositorySerializer
from builder.models import Build, BranchBuild, Deploy, Environment, Site
from builder.serializers import BranchBuildSerializer, FlatSiteSerializer, \
    SiteSerializer
from core.helpers import do_auth, validate_request_payload
from users.serializers import UserSerializer


logger = logging.getLogger(__name__)


class ProjectList(APIView):
    """
    Get all repos currently deployed by Franklin that the user can manage or
    register a new repo
    """
    permission_classes = (UserIsProjectAdmin,)

    def get(self, request, format=None):
        sites = request.user.details.get_user_repos()
        site_serializer = FlatSiteSerializer(sites, many=True)
        return Response(site_serializer.data, status=status.HTTP_200_OK)

    @validate_request_payload(['github', ])
    def post(self, request, format=None):
        project = request.data['github']
        owner, repo = project.split('/')
        if Site.objects.filter(name=repo, owner__name=owner).count() > 0:
            return Response({'detail': 'Resource already exists'}, status=422)

        test_owner = type("", (object,), {})()
        test_owner.name = owner
        test_site = type("", (object,), {})()
        test_site.name = repo
        test_site.owner = test_owner
        self.check_object_permissions(request, test_site)

        # New project, call github for the details
        result = get_repo(owner, repo, request.user)
        if status.is_success(result.status_code):
            serializer = RepositorySerializer(data=result.json())
            if serializer and serializer.is_valid():
                site = serializer.save()

                # Call Github to register a webhook
                webhook_r = create_repo_webhook(site, request.user)
                if (status.is_success(webhook_r.status_code) or
                        webhook_r.status_code == 422):
                    site.webhook_id = webhook_r.json().get('id', '')
                    # Call Github to register a deploy key
                    deploy_key_r = create_repo_deploy_key(site, request.user)
                    if (status.is_success(deploy_key_r.status_code) or
                            deploy_key_r.status_code == 422):
                        site.deploy_key_id = deploy_key_r.json().get('id', '')
                        site.save(user=request.user)
                        site_serializer = SiteSerializer(
                                site, context={'user': request.user})
                        return Response(site_serializer.data,
                                        status=status.HTTP_201_CREATED)
                delete_site(site, request.user)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProjectDetail(APIView):
    """
    Rerieve or Delete a Github project with franklin
    """
    permission_classes = (UserIsProjectAdmin,)

    def get_object(self, pk):
        try:
            return Site.objects.get(github_id=pk)
        except Site.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        site = self.get_object(pk)
        site_serializer = SiteSerializer(site, context={'user': request.user})
        return Response(site_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, format=None):
        site = self.get_object(pk)
        # Before proceeding, check that user is allowed
        self.check_object_permissions(request, site)
        site.is_active = False
        site.save()
        return delete_site(site, request.user)


def delete_site(site, user):
    # TODO - This should be an async process that is thrown into a queue. The
    # site is no longer active, so the actual delete can occur lazily.
    webhook_deleted = delete_webhook(site, user)
    if webhook_deleted and status.is_success(webhook_deleted.status_code):
        deploy_key_delete_response = delete_deploy_key(site, user)
        if status.is_success(deploy_key_delete_response.status_code):
            site.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            message = 'Github deleted the webhook, but not the deploy key'
            logger.warn(message + ' | %s | %s', user, site)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def deployable_repos(request):
    """
    All repos from Github that the user has the permission level to deploy
    """
    if request.method == 'GET':
        github_repos = get_all_repos(request.user)
        serializer = RepositorySerializer(github_repos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def builds(request, pk):
    """
    Deploy the tip of the default branch for the project or return all builds
    that exist for the project
    """
    try:
        site = Site.objects.get(github_id=pk)
    except Site.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        builds = BranchBuild.objects.filter(site=site).all()
        serializer = BranchBuildSerializer(builds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        try:
            branch, git_hash = site.get_newest_commit(request.user)
            environment = site.environments.filter(name='Staging').first()
            build, created = BranchBuild.objects.get_or_create(
                git_hash=git_hash, branch=branch, site=site)
            build.deploy(environment)
            serializer = BranchBuildSerializer(build)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            logger.warning("Failed project tip deploy - %s", sys.exc_info()[0])
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PromoteEnvironment(APIView):
    """
    Promote a build to a higher environment
    """
    def get_object(self, request, repo, env):
        try:
            site = Site.objects.get(github_id=repo)
            environment = Environment.objects.get(name__iexact=env, site=site)
            git_hash = request.data['git_hash']
            build = BranchBuild.objects.get(git_hash=git_hash)
            return (environment, build)
        except (BranchBuild.DoesNotExist, Environment.DoesNotExist,
                Site.DoesNotExist) as e:
            raise NotFound(detail=e)

    @validate_request_payload(['git_hash', ])
    def post(self, request, repo, env, format=None):
        environment, build = self.get_object(request, repo, env)
        current_deploy = environment.get_current_deploy()
        message = {}
        if current_deploy and build.id == current_deploy.id:
            message = {'detail': 'already deployed'}
        elif environment.name == 'Production':
            if build.status == Build.SUCCESS and build.environments.exists():
                Deploy.objects.create(build=build, environment=environment)
                return Response(status=status.HTTP_201_CREATED)
            message = {'detail': 'build is not suitable for promotion'}
        else:
            # Must be staging
            if build.status == Build.SUCCESS and build.environments.exists():
                Deploy.objects.create(build=build, environment=environment)
                return Response(status=status.HTTP_201_CREATED)
            elif build.status == Build.FAILED:
                build.deploy(environment)
                return Response(status=status.HTTP_201_CREATED)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


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
                    github_event.attempt_deployment()
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    logger.warning("Received invalid Github Webhook message")
                # Likely a webhook we don't build for.
                return Response(status=status.HTTP_200_OK)
            elif event_type == 'ping':
                # We COULD update the DB with some important info here
                # repository{ id, name, owner{ id, login },
                #             sender{ id, login, site_admin }}
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            logger.warning("Received a malformed POST message")
    else:
        # Invalid methods are caught at a higher level
        pass
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes((AllowAny, ))
def get_auth_token(request):
    """
    View to authenticate with github using a client code
    """
    if request.method == 'GET':
        message = {'client_id': os.environ['SOCIAL_AUTH_GITHUB_KEY']}
        return Response(message, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        response = get_access_token(request)
        if status.is_success(response.status_code):
            try:
                access_token = response.json().get('access_token', None)
                user = do_auth(access_token)
                serializer = UserSerializer(user)
                response_data = Response({
                    'token': access_token,
                    'user': serializer.data
                }, status=status.HTTP_200_OK)
            except KeyError:
                response_data = Response(status=status.HTTP_400_BAD_REQUEST)
            return response_data
        return Response(status=response.status_code)
