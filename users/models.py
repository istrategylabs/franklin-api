from django.db import models


class User(models.Model):
    """ Represents an authenticated 'user' that allows us to utilize Github
    webhooks from their repos.

    :param username: The user's unique username (taken from github)
    :param github_token: The user's stored github auth token
    """
    username = models.CharField(max_length=30)
    github_token = models.CharField(max_length=30)

    def __unicode__(self):
        return self.username
