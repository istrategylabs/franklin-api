
import hmac
import hashlib
import os

from rest_framework import permissions

from .api import get_repo_permissions


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


class UserIsProjectAdmin(permissions.BasePermission):
    """ Security Check that the POSTing user is an admin for the project"""

    def has_object_permission(self, request, view, obj):
        if request.method not in ['POST', 'DELETE']:
            return True
        perms = get_repo_permissions(obj.owner.name, obj.name, request.user)
        if perms.get('admin', False):
            return True
        return False
