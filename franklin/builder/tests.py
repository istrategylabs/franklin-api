import os
from unittest import mock

from django.test import TestCase

from .models import BranchBuild, Environment, Owner, Site, TagBuild
from github.serializers import GithubWebhookSerializer


class OwnerTestCase(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)

    def test_owner_creation(self):
        self.assertEqual(self.owner.name, "istrategylabs")


class EnvironmentTestCase(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)
        self.env = self.site.environments.get(name=self.site.DEFAULT_ENV)
        self.git_message = dict([('ref', 'refs/heads/master'),
                                ('head_commit', dict([('id', '80d25a09bc1ceb7d6707048211745dcc01bc8705')])),
                                ('repository', dict([('id', '36470460'),
                                                    ('full_name', 'istrategylabs/franklin-dashboard')]))])

    def test_has_default_env(self):
        self.assertTrue(self.site.environments
                            .filter(name=self.site.DEFAULT_ENV).exists())

    def test_env_url_default_empty(self):
        """ Until the environment has a deployment, the url should not exist in
        the db
        """
        self.assertEqual(self.env.url, '')

    def test_get_deployable_event_branch(self):
        """ Tests the model method that should return an environment after
        correctly validating a branch push event from github
        """
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            self.assertEqual(matching_env, self.env)
        else:
            self.fail(github_event.errors)

    def test_get_deployable_event_wrong_branch(self):
        """ Tests the model method does not return an environment after
        correctly validating a branch push event from github for a
        non-registered branch
        """
        self.git_message['ref'] = 'refs/heads/staging'
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            self.assertIsNone(matching_env)
        else:
            self.fail(github_event.errors)

    def test_get_deployable_event_tag(self):
        """ Tests the model method that should return an environment after
        correctly validating a tag event from github
        """
        # Also our default production env to only deploy on tags
        self.env.deploy_type = Environment.TAG
        self.env.tag_regex = 'v[0-9]\.[0-9]\.[0-9]'
        self.env.save()
        # Alter our github payload to be a tag event
        self.git_message['ref'] = 'v1.0.2'
        self.git_message['ref_type'] = 'tag'
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            self.assertEqual(matching_env, self.env)
        else:
            self.fail(github_event.errors)

    @mock.patch('core.helpers.requests.post')
    def test_building_env(self, mock_post):
        """ Tests the model method that calls franklin-builder when an
        environment is ready to be deployed for a branch.
        """
        # Mock the POST request to builder
        response = mock.Mock()
        response.status_code = 200
        mock_post.return_value = response

        self.assertEqual(self.env.status, Environment.REGISTERED)
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            matching_env.build()
        self.assertEqual(matching_env.status, Environment.BUILDING)

    @mock.patch('core.helpers.requests.post')
    def test_building_env_negative(self, mock_post):
        """ Tests the model method that calls franklin-builder when builder
        returns an error.
        """
        # Mock the POST request to builder
        response = mock.Mock()
        response.status_code = 500
        mock_post.return_value = response

        self.assertEqual(self.env.status, Environment.REGISTERED)
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            matching_env.build()
        self.assertEqual(matching_env.status, Environment.FAILED)

    @mock.patch('core.helpers.requests.post')
    def test_building_env_tag(self, mock_post):
        """ Tests the model method that calls franklin-builder when an
        environment is ready to be deployed for a tag.
        """
        # Mock the POST request to builder
        response = mock.Mock()
        response.status_code = 200
        mock_post.return_value = response

        self.assertEqual(self.env.status, Environment.REGISTERED)
        self.env.deploy_type = Environment.TAG
        self.env.tag_regex = 'v[0-9]\.[0-9]\.[0-9]'
        self.env.save()
        # Alter our github payload to be a tag event
        self.git_message['ref'] = 'v1.0.2'
        self.git_message['ref_type'] = 'tag'
        github_event = GithubWebhookSerializer(data=self.git_message)
        if github_event.is_valid():
            matching_env = self.site.get_deployable_event(github_event)
            matching_env.build()
        self.assertEqual(matching_env.status, Environment.BUILDING)


class BuildTestCase(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)
        self.env = self.site.environments.get(name=self.site.DEFAULT_ENV)
        self.tag_build = TagBuild.objects.create(tag='v1.0.2', site=self.site)
        self.branch_build = BranchBuild.objects.create(
            git_hash='asdf1234', branch='master', site=self.site)

    def test_tag_build_path(self):
        """ Test that object instantiation saves correct path. """
        expected = "{base}/{owner}/{site}/{tag}".format(
            base=os.environ['BASE_PROJECT_PATH'], owner=self.site.owner.name,
            site=self.site.name, tag='v102')
        self.assertEqual(self.tag_build.path, expected)

    def test_branch_build_path(self):
        """ Test that object instantiation saves correct path. """
        expected = "{base}/{owner}/{site}/{git_hash}".format(
            base=os.environ['BASE_PROJECT_PATH'], owner=self.site.owner.name,
            site=self.site.name, git_hash='asdf1234')
        self.assertEqual(self.branch_build.path, expected)

    def test_env_url_exists(self):
        """ Tests that the url exists after the environment has a deployment
        """
        self.env.current_deploy = self.tag_build
        self.env.save()
        expected = "{name}.{base_domain}".format(
            name=self.site.name, base_domain=os.environ['BASE_URL'])
        self.assertEqual(self.env.url, expected)

    def test_extra_env_url_exists(self):
        """ Tests that the non-prod urls exist and are look right
        """
        new_env = self.site.environments.create(name="foo")
        new_env.current_deploy = self.branch_build
        new_env.save()
        expected = "{name}-{env}.{base_domain}".format(
            name=self.site.name, env=new_env.name,
            base_domain=os.environ['BASE_URL'])
        self.assertEqual(new_env.url, expected)

    def test_past_builds_lookup(self):
        """ Tests that when a build is added as the current deploy for an
        environment, it's also added to the list of past builds
        """
        self.env.current_deploy = self.tag_build
        self.env.save()
        self.assertTrue(self.env.past_builds
                            .filter(pk=self.env.current_deploy.pk).exists())
