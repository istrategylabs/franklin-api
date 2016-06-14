import os
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Build, BranchBuild, Deploy, Environment, Owner, Site
from core.exceptions import ServiceUnavailable
from github.serializers import GithubWebhookSerializer


class OwnerTestCase(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)

    def test_owner_creation(self):
        self.assertEqual(self.owner.name, "istrategylabs")


class SiteTestCase(TestCase):
    @mock.patch('core.helpers.requests.get')
    def setUp(self, mock_get):
        # mocking the return object from POSTing to github API
        mock_get_response = mock.Mock(status_code=200)
        mock_get_response.json.return_value = {"default_branch": "master"}
        mock_get.return_value = mock_get_response

        self.user = User.objects.create_user(username="testuser", password="a")
        social = self.user.social_auth.create(provider='github')
        social.extra_data['access_token'] = ''
        social.save()

        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)

        self.site.save(user=self.user)
        self.env = self.site.environments.get(name='Staging')
        self.git_message = dict([('ref', 'refs/heads/master'),
                                ('head_commit', dict([('id', '80d25a09bc1ceb7d6707048211745dcc01bc8705')])),
                                ('repository', dict([('id', '36470460'),
                                                     ('full_name', 'istrategylabs/franklin-dashboard'),
                                                     ('owner', dict([('id', '234234123'),
                                                                     ('login', 'istrategylabs')])),
                                                     ('html_url', 'http://github.com/istrategylabs/franklin-dashboard'),
                                                     ('name', 'franklin-dashboard')]))])

    def test_has_default_env(self):
        """ All sites should start with a production environment on creation
        """
        self.assertTrue(self.site.environments
                            .filter(name=self.site.DEFAULT_ENV).exists())

    def test_get_deployable_environment_branch(self):
        """ Tests the model method that should return an environment after
        correctly validating a branch push event from github
        """
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            event = github_event.get_change_location()
            is_tag_event = github_event.is_tag_event()
            matching_env = self.site.get_deployable_environment(
                event, is_tag_event)
            self.assertEqual(matching_env, self.env)
        else:
            self.fail(github_event.errors)

    def test_get_deployable_environment_wrong_branch(self):
        """ Tests the model method does not return an environment after
        correctly validating a branch push event from github for a
        non-registered branch
        """
        self.git_message['ref'] = 'refs/heads/staging'
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            event = github_event.get_change_location()
            is_tag_event = github_event.is_tag_event()
            matching_env = self.site.get_deployable_environment(
                event, is_tag_event)
            self.assertIsNone(matching_env)
        else:
            self.fail(github_event.errors)


class EnvironmentTestCase(TestCase):
    @mock.patch('core.helpers.requests.get')
    def setUp(self, mock_get):
        # mocking the return object from POSTing to github API
        mock_get_response = mock.Mock(status_code=200)
        mock_get_response.json.return_value = {"default_branch": "master"}
        mock_get.return_value = mock_get_response

        self.user = User.objects.create_user(username="testuser", password="a")
        social = self.user.social_auth.create(provider='github')
        social.extra_data['access_token'] = ''
        social.save()

        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='FrAnKlIn-DaShBoArD', github_id=45864453)
        self.site.save(user=self.user)
        self.env = self.site.environments.get(name=self.site.DEFAULT_ENV)
        self.branch_build = BranchBuild.objects.create(
            git_hash='asdf1234', branch=self.env.branch, site=self.site)

    def test_past_builds(self):
        """ Current deployment is always added to past builds on save.
        """
        self.assertFalse(self.env.past_builds.exists())
        Deploy.objects.create(build=self.branch_build, environment=self.env)
        self.assertTrue(self.env.past_builds.exists())

    def test_production_env_url(self):
        """ Production environments have a special url.
        """
        expected = "{name}.{base_domain}".format(
            name=self.site.name.lower(), base_domain=os.environ['BASE_URL'])
        self.assertEqual(self.env.url, expected)

    def test_env_url(self):
        """ Environment should have a URL on save.
        """
        new_env = Environment.objects.create(name='Bleh', site=self.site)
        expected = "{name}-{env}.{base_domain}".format(
            name=self.site.name.lower(), env=new_env.name.lower(),
            base_domain=os.environ['BASE_URL'])
        self.assertEqual(new_env.url, expected)


class BuildTestCase(TestCase):

    @mock.patch('core.helpers.requests.get')
    def setUp(self, mock_get):
        # mocking the return object from POSTing to github API
        mock_get_response = mock.Mock(status_code=200)
        mock_get_response.json.return_value = {"default_branch": "master"}
        mock_get.return_value = mock_get_response

        self.user = User.objects.create_user(username="testuser", password="a")
        social = self.user.social_auth.create(provider='github')
        social.extra_data['access_token'] = ''
        social.save()

        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)
        self.site.save(user=self.user)
        self.env = self.site.environments.filter(name=self.site.DEFAULT_ENV)\
                                         .first()
        self.branch_build = BranchBuild.objects.create(
            git_hash='asdf1234', branch='master', site=self.site)

    def test_branch_build_path(self):
        """ Test that object instantiation saves correct path. """
        expected = "{site}/{uuid}".format(site=self.site.github_id,
                                          uuid=self.branch_build.uuid)
        self.assertEqual(self.branch_build.path, expected)

    def test_default_build_status(self):
        """ All build objects start with a status of new on creation
        """
        self.assertEqual(self.branch_build.status, Build.NEW)

    @mock.patch('core.helpers.requests.post')
    def test_building_env(self, mock_post):
        """ Tests the model method that calls franklin-builder when an
        environment is ready to be deployed for a branch.
        """
        mock_post.return_value = mock.Mock(status_code=200)

        self.branch_build.deploy(self.env)
        self.assertEqual(self.branch_build.status, Build.BUILDING)

    @mock.patch('core.helpers.requests.post')
    def test_building_env_negative(self, mock_post):
        """ Tests the model method that calls franklin-builder when builder
        returns an error.
        """
        mock_post.return_value = mock.Mock(status_code=500)

        with self.assertRaises(ServiceUnavailable):
            self.branch_build.deploy(self.env)
        self.assertEqual(self.branch_build.status, Build.NEW)
