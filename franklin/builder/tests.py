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


class SiteTestCase(TestCase):
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
        """ All sites should start with a production environment on creation
        """
        self.assertTrue(self.site.environments
                            .filter(name=self.site.DEFAULT_ENV).exists())

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


class EnvironmentTestCase(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='FrAnKlIn-DaShBoArD', github_id=45864453)
        self.env = self.site.environments.get(name=self.site.DEFAULT_ENV)
        self.branch_build = BranchBuild.objects.create(
            git_hash='asdf1234', branch=self.env.branch, site=self.site)
        self.env.current_deploy = self.branch_build

    def test_past_builds(self):
        """ Current deployment is always added to past builds on save.
        """
        self.assertFalse(self.env.past_builds.exists())
        self.env.save()
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
        staging = Environment.objects.create(name='Staging', site=self.site)
        expected = "{name}-{env}.{base_domain}".format(
            name=self.site.name.lower(), env=staging.name.lower(),
            base_domain=os.environ['BASE_URL'])
        self.assertEqual(staging.url, expected)

    def test_default_env_status(self):
        """ All environments start with a status of registered on creation
        """
        self.assertEqual(self.env.status, Environment.REGISTERED)

    @mock.patch('core.helpers.requests.post')
    def test_building_env(self, mock_post):
        """ Tests the model method that calls franklin-builder when an
        environment is ready to be deployed for a branch.
        """
        mock_post.return_value = mock.Mock(status_code=200)

        self.env.build()
        self.assertEqual(self.env.status, Environment.BUILDING)

    @mock.patch('core.helpers.requests.post')
    def test_building_env_negative(self, mock_post):
        """ Tests the model method that calls franklin-builder when builder
        returns an error.
        """
        mock_post.return_value = mock.Mock(status_code=500)

        self.env.build()
        self.assertEqual(self.env.status, Environment.FAILED)

    @mock.patch('core.helpers.requests.post')
    def test_building_env_tag(self, mock_post):
        """ Tests the model method that calls franklin-builder when an
        environment is ready to be deployed for a tag.
        """
        mock_post.return_value = mock.Mock(status_code=200)

        # Create a tag event build
        tag_build = TagBuild.objects.create(tag='v1.0.2', site=self.site)
        self.env.current_deploy = tag_build

        self.env.build()
        self.assertEqual(self.env.status, Environment.BUILDING)


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

    def test_past_builds_lookup(self):
        """ Tests that when a build is added as the current deploy for an
        environment, it's also added to the list of past builds
        """
        self.env.current_deploy = self.tag_build
        self.env.save()
        self.assertTrue(self.env.past_builds
                            .filter(pk=self.env.current_deploy.pk).exists())
