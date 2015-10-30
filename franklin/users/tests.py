from django.contrib.auth.models import User
from django.test import TestCase

from .models import UserDetails

class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="asdf")

    def test_user_details_creation(self):
        """ Every user that is created should have details
        """
        self.assertIsInstance(self.user.details, UserDetails)
