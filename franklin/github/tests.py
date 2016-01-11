from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from rest_framework import status

from .views import get_auth_token, get_franklin_config
from builder.models import Owner, Site


class ConfigTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="asdf")
        social = self.user.social_auth.create(provider='github')
        social.extra_data['access_token'] = ''
        social.save()
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)

    @mock.patch('github.views.make_rest_get_call')
    def test_get_franklin_config(self, mock_get):
        """ Tests the method to retrieve project specific franklin config
        """
        # Mock the first GET call to retrieve the file URL
        mock_url = mock.Mock()
        mock_url.status_code = 200
        expected_dict = {"download_url": "http://www.google.com/"}
        mock_url.json.return_value = expected_dict

        # Mock the second GET call to retrieve the file contents
        mock_file_data = mock.Mock()
        mock_file_data.status_code = 200
        mock_file_data.text = "hello: 'world'"
        mock_get.side_effect = [mock_url, mock_file_data]

        franklin_config = get_franklin_config(self.site, self.user)
        if franklin_config and not hasattr(franklin_config, 'status_code'):
            self.assertEqual(franklin_config.get('hello', None), 'world')
        else:
            self.fail('Received an HTTP Response instead of data from method')


class OauthTokenTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="a")
        social = self.user.social_auth.create(provider='github')
        social.extra_data['access_token'] = ''
        social.save()
        self.owner = Owner.objects.create(
            name='istrategylabs', github_id=607333)
        self.site = Site.objects.create(
            owner=self.owner, name='franklin-dashboard', github_id=45864453)

    @mock.patch('github.views.do_auth')
    @mock.patch('github.views.make_rest_post_call')
    def test_get_franklin_config(self, mock_post, mock_auth):
        """ Tests the method to fetch an oauth token
        """
        # mocking a request object received by the API
        request = self.factory.post('/auth/github')
        request.data = {'code': 'asdf',
                        'clientId': 'asdf',
                        'redirectUrl': 'asdf'}

        # mocking the return object from POSTing to github API
        mock_post_response = mock.Mock(status_code=200)
        mock_post_response.json.return_value = {"access_token": "testtoken"}
        mock_post.return_value = mock_post_response

        # mocking the do_auth method to just return our user
        mock_auth.return_value = self.user

        response = get_auth_token(request)
        if response and status.is_success(response.status_code):
            self.assertEqual(response.data['token'], 'testtoken')
            user = response.data.get('user', None)
            self.assertIsNotNone(user)
            self.assertEqual(user['username'], 'testuser')
        else:
            self.fail('Received a bad HTTP Response object')
