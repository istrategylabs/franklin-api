import hmac
import hashlib
import os

from rest_framework import permissions
from rest_framework.exceptions import NotFound

from .api import get_repo_permissions
from builder.models import Site
from core.exceptions import BadRequest


class GithubOnly(permissions.BasePermission):
    """ Security Check for certain API endpoints only called by Github."""

    def has_permission(self, request, view):
        secret = request.META.get("HTTP_X_HUB_SIGNATURE")
        if secret:
            # must convert to bytes for python 3.5 bug in hmac library
            key = bytes(os.environ['GITHUB_SECRET'].encode('ascii'))
            computed_secret = 'sha1=' + hmac.new(
                key, request.body, hashlib.sha1).hexdigest()
            return hmac.compare_digest(computed_secret, secret)
        return False


class UserHasProjectWritePermission(permissions.BasePermission):
    """ Security Check - user is an admin for the project; can create/delete"""

    def check_perms(self, user, repo, owner):
        if user and repo and owner:
            # Call github and confirm user is an admin for this project
            perms = get_repo_permissions(owner, repo, user)
            if perms.get('admin', False):
                return True
        return False

    def has_permission(self, request, view):
        # Read-Only ops (GET, OPTIONS, HEAD) pass for logged in users
        if request.method in permissions.SAFE_METHODS:
            return True
        try:
            if request.method == 'POST':
                obj = request.data['github'].split('/')
                return self.check_perms(request.user, obj[1], obj[0])
            elif request.method == 'DELETE':
                obj = Site.objects.get(github_id=view.kwargs['repo'])
                return self.check_perms(request.user, obj.name, obj.owner.name)
        except (KeyError, IndexError):
            raise BadRequest()
        except Site.DoesNotExist as e:
            raise NotFound(detail=e)
        return False

    def has_object_permission(self, request, view, site):
        return self.check_perms(request.user, site.name, site.owner.name)
