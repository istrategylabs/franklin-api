from datetime import datetime
import json

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from builder.models import BranchBuild, Build, Deploy, Environment, Owner, Site


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def get_mock_data(location, method):
    path = 'github/mock_data/{0}/{1}.json'.format(location, method)
    with open(path) as json_file:
        return json.load(json_file)


class v1ContractTestCase(APITestCase):
    """
    WARNING: Making changes to these tests may break expected user
    functionality for calls to the v1 of the API and thus break the implied
    service contract.
    Code changes that effect these tests should be made with great care.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="a")

        token = 'abc123'
        self.header = {'HTTP_AUTHORIZATION': 'Bearer {}'.format(token)}
        social = self.user.social_auth.create(provider='github', uid=123)
        social.extra_data['access_token'] = token
        social.save()

        self.owner = Owner.objects.create(name='isl', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='foo', github_id=45864453)
        Environment.objects.create(site=self.site, name='Production',
                                   url='foo.example.com')
        self.env = Environment.objects.create(site=self.site, name='Staging',
                                              url='foo-staging.example.com')

    def test_get_auth_github(self):
        """ Get public app key for calling github """
        url = '/v1/auth/github/'
        self.assertEqual(reverse('get_token'), url)

        expected = {'client_id': 'foo'}

        with patch.dict('os.environ', {'SOCIAL_AUTH_GITHUB_KEY': 'foo'}):
            response = self.client.get(url)

        self.assertEqual(expected, response.data)

    @patch('github.views.do_auth')
    @patch('core.helpers.requests.post')
    def test_post_auth_github(self, mock_post, mock_auth):
        """ Complete auth with temp token. Retrieve oAuth token  """
        url = '/v1/auth/github/'
        self.assertEqual(reverse('get_token'), url)

        # mocking the return object from POSTing to github API
        mock_post_response = Mock(status_code=200)
        mock_post_response.json.return_value = {"access_token": "testtoken"}
        mock_post.return_value = mock_post_response

        # mocking the do_auth method to just return our user
        mock_auth.return_value = self.user

        expected = {'user': {'username': 'testuser'}, 'token': 'testtoken'}
        response = self.client.post(url, {
            'code': 'asdf',
            'clientId': 'asdf',
            'redirectUrl': 'asdf'
        }, **self.header)

        self.assertEqual(expected, response.data)

    def test_get_user_details(self):
        """ Returns details about the user who owns the passed token """
        url = '/v1/user/'
        self.assertEqual(reverse('user_details'), url)

        expected = {'username': 'testuser'}
        response = self.client.get(url, **self.header)

        self.assertEqual(expected, response.data)

    @patch('core.helpers.requests.get')
    def test_get_users_repos(self, mock_get):
        """ Get repos from github that the user has access to """
        url = '/v1/repos/'
        self.assertEqual(reverse('deployable_repos'), url)

        expected = get_mock_data('github', 'get_repos')

        # get list of repos from github
        get_repos = Mock(status_code=200)
        get_repos.json.return_value = expected
        mock_get.return_value = get_repos

        response = self.client.get(url, **self.header)

        self.assertEqual(expected, response.data)

    @patch('core.helpers.requests.post')
    @patch('core.helpers.requests.get')
    def test_post_projects(self, mock_get, mock_post):
        """ Register a project """
        url = '/v1/projects/'
        self.assertEqual(reverse('project_list'), url)

        # Repo details from github
        get_repo = Mock(status_code=200)
        get_repo.json.return_value = get_mock_data('github', 'get_repo')
        mock_get.return_value = get_repo

        # Creating webhook and deploy key on github repo
        post_github = Mock(status_code=200)
        post_github.json.return_value = {'id': 123}
        mock_post.return_value = post_github

        expected = get_mock_data('api_responses', 'new_site')
        with patch.dict('os.environ', {'BASE_URL': 'example.com'}):
            response = self.client.post(url, {'github': 'isl/bar'},
                                        **self.header)

        self.assertEqual(ordered(expected), ordered(response.data))

    @patch('core.helpers.requests.get')
    def test_get_projects(self, mock_get):
        """ List of registered projects """
        url = '/v1/projects/'
        self.assertEqual(reverse('project_list'), url)

        # users orgs from github
        get_repo = Mock(status_code=200)
        get_repo.json.return_value = get_mock_data('github', 'get_user_orgs')
        mock_get.return_value = get_repo

        expected = get_mock_data('api_responses', 'projects')
        response = self.client.get(url, **self.header)

        self.assertEqual(ordered(expected), ordered(response.data))

    @patch('core.helpers.requests.get')
    @patch('core.helpers.requests.delete')
    def test_delete_project(self, mock_delete, mock_get):
        """ Delete a project that is already registered """
        url = '/v1/projects/45864453'
        self.assertEqual(reverse('project_details', args=['45864453', ]), url)

        # Repo details from github
        get_repo = Mock(status_code=200)
        get_repo.json.return_value = get_mock_data('github', 'get_repo')
        mock_get.return_value = get_repo

        # attempts to call github to delete webhook and deploy key
        mock_delete.return_value = Mock(status_code=204)

        response = self.client.delete(url, **self.header)
        self.assertEqual(204, response.status_code)

    @patch('core.helpers.requests.get')
    def test_get_project_details(self, mock_get):
        """ Returns details for a project that is registered """
        url = '/v1/projects/45864453'
        self.assertEqual(reverse('project_details', args=['45864453', ]), url)

        # Repo details from github
        get_repo = Mock(status_code=200)
        get_repo.json.return_value = get_mock_data('github', 'get_repo')
        mock_get.return_value = get_repo

        expected = get_mock_data('api_responses', 'new_site')
        with patch.dict('os.environ', {'BASE_URL': 'example.com'}):
            response = self.client.get(url, **self.header)

        self.assertEqual(ordered(expected), ordered(response.data))

    @patch('core.helpers.requests.post')
    @patch('core.helpers.requests.get')
    def test_deploy_project(self, mock_get, mock_post):
        """ Attempts to deploy the latest commit for the project """
        url = '/v1/projects/45864453/builds'
        self.assertEqual(reverse('project_builds', args=['45864453', ]), url)

        # Repo details from github
        get_repo = Mock(status_code=200)
        get_repo.json.return_value = get_mock_data('github', 'get_repo')

        # branch details from github
        get_branch = Mock(status_code=200)
        get_branch.json.return_value = get_mock_data('github', 'get_branch')

        mock_get.side_effect = [get_repo, get_branch]

        # Creating webhook and deploy key on github repo
        mock_post.return_value = Mock(status_code=200)

        expected = get_mock_data('api_responses', 'build')
        # Build object has an auto-generated creation date. mock that.
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2016, 5, 4)
            response = self.client.post(url, **self.header)

        self.assertEqual(ordered(expected), ordered(response.data))

    def test_get_projects_builds(self):
        """ Returns a list of all build objects attached to the project """
        url = '/v1/projects/45864453/builds'
        self.assertEqual(reverse('project_builds', args=['45864453', ]), url)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2016, 5, 4)
            BranchBuild.objects.create(
                site=self.site, branch='staging', status=Build.BUILDING,
                git_hash='d4f846545faa92894c6bf39dada28023b6ff9418')

        expected = get_mock_data('api_responses', 'builds')
        response = self.client.get(url, **self.header)

        self.assertEqual(ordered(expected), ordered(response.data))

    def test_promote_build(self):
        """ Attempts to promote a successful build to a given environment """
        url = '/v1/projects/45864453/environments/production'
        self.assertEqual(reverse('promote_environment',
                         args=['45864453', 'production']), url)

        build = BranchBuild.objects.create(
            site=self.site, branch='staging', status=Build.SUCCESS,
            git_hash='abc123')
        Deploy.objects.create(build=build, environment=self.env)
        response = self.client.post(url, {"uuid": build.uuid}, **self.header)

        self.assertEqual(201, response.status_code)
