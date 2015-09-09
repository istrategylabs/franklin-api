import os

from django.test import TestCase

from .models import Site


class SitesTestCase(TestCase):
    def setUp(self):
        Site.objects.create(git_hash='123ABC', repo_name='example/test')

    def test_site_path(self):
        """ Test that object instantiation saves correct path. """
        s = Site.objects.get(git_hash='123ABC')
        print(s)
        expected = "{base}/{repo_name}".format(
            base=os.environ['BASE_PROJECT_PATH'],
            repo_name=s.repo_name
        )
        self.assertEqual(s.path, expected)

    def test_site_url(self):
        """ Tests that the url does not include the full repo_name
        and only the name without the owner
        """
        s = Site.objects.get(git_hash='123ABC')
        repo_name = s.repo_name.split("/")[1]
        expected = "{name}.{base_domain}".format(
            name=repo_name,
            base_domain=os.environ['BASE_URL']
        )
        self.assertEqual(s.url, expected)
