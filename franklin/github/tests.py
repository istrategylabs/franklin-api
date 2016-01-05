from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from .views import get_franklin_config
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
