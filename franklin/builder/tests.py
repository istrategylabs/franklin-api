import os

from django.test import TestCase

from .models import Site


class SitesTestCase(TestCase):
    def setUp(self):
        Site.objects.create(git_hash='123ABC', repo_name='test')

    def test_site_path(self):
        """ Test that object instantiation saves correct path. """
        s = Site.objects.get(git_hash='123ABC')
        expected = "{base}/{id}".format(base=os.environ['BASE_PROJECT_PATH'],
                                        id=s.id)
        self.assertEqual(s.path, expected)
