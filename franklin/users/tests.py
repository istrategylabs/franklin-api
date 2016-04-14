from unittest import mock
from django.contrib.auth.models import User
from django.test import TestCase

from .models import UserDetails
from builder.models import Owner, Site


class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="asdf")
        self.owner = Owner.objects.create(name='owner', github_id=1)
        self.site = Site.objects.create(
            name='project', github_id=2, owner=self.owner)
        # Mock response from github for user's repo list
        self.repos = []
        repo_data = {}
        repo_data['id'] = self.site.github_id
        repo_data['name'] = self.site.name
        repo_data['url'] = 'http://github.com/path/to/project'
        repo_data['owner'] = {}
        repo_data['owner']['name'] = 'owner'
        repo_data['owner']['id'] = 2
        repo_data['permissions'] = {}
        repo_data['permissions']['admin'] = True
        self.repos.append(repo_data)
        UserDetails.get_user_repos = mock.Mock(return_value=self.repos)

    def test_user_details_creation(self):
        """ Every user that is created should have details
        """
        self.assertIsInstance(self.user.details, UserDetails)
