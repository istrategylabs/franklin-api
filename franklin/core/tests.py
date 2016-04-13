import os
from requests.exceptions import ConnectionError, HTTPError, Timeout
from unittest import mock

from django.test import TestCase

from .exceptions import ServiceUnavailable
from .helpers import make_rest_get_call, make_rest_post_call


class HelpersTestCase(TestCase):
    def setUp(self):
        self.url = os.environ['BUILDER_URL'] + '/build'
        self.headers = {'content-type': 'application/json'}
        self.body = {
            "deploy_key": "deploy_key",
            "branch": "branch",
            "tag": "tag",
            "git_hash": "git_hash",
            "repo_owner": "owner",
            "path": "path",
            "repo_name": "name",
            "environment_id": 1
            }

    @mock.patch('core.helpers.requests.post', side_effect=ConnectionError)
    def test_make_rest_post_call_conn_error(self, mock_post):
        """ Tests make_rest_post_call when the call has an Connection exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_post_call(self.url, self.headers, self.body)

    @mock.patch('core.helpers.requests.post', side_effect=HTTPError)
    def test_make_rest_post_call_http_error(self, mock_post):
        """ Tests make_rest_post_call when the call has an HTTP exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_post_call(self.url, self.headers, self.body)

    @mock.patch('core.helpers.requests.post', side_effect=Timeout)
    def test_make_rest_post_call_timeout_error(self, mock_post):
        """ Tests make_rest_post_call when the call has an Timeout exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_post_call(self.url, self.headers, self.body)

    @mock.patch('core.helpers.requests.post')
    def test_make_rest_post_call_error(self, mock_post):
        """ Tests make_rest_post_call when the api returns some error
        """
        # Mock the POST request to builder
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        response = make_rest_post_call(self.url, self.headers, self.body)
        self.assertEqual(response.status_code, 400)

    @mock.patch('core.helpers.requests.get', side_effect=ConnectionError)
    def test_make_rest_get_call_conn_error(self, mock_post):
        """ Tests make_rest_get_call when the call has an Connection exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_get_call(self.url, self.headers)

    @mock.patch('core.helpers.requests.get', side_effect=HTTPError)
    def test_make_rest_get_call_http_error(self, mock_post):
        """ Tests make_rest_get_call when the call has an HTTP exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_get_call(self.url, self.headers)

    @mock.patch('core.helpers.requests.get', side_effect=Timeout)
    def test_make_rest_get_call_timeout_error(self, mock_post):
        """ Tests make_rest_get_call when the call has an Timeout exception.
        """
        with self.assertRaises(ServiceUnavailable):
            make_rest_get_call(self.url, self.headers)

    @mock.patch('core.helpers.requests.get')
    def test_make_rest_get_call_error(self, mock_post):
        """ Tests make_rest_get_call when the api returns some error
        """
        # Mock the POST request to builder
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        response = make_rest_get_call(self.url, self.headers)
        self.assertEqual(response.status_code, 400)
