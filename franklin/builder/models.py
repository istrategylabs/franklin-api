import json
import logging
import os
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import sys
import uuid

from django.db import models

from rest_framework import status

logger = logging.getLogger(__name__)


class Site(models.Model):
    """ Represents a 'deployed' or soon-to-be deployed static site.

    :param id: A unique site identified
    :param owner: The name of the owner of the repo on github. (User or Org)
    :param owner_id: Unqiue ID github has assigned the owner
    :param repo_name: The name of the project on github
    :param repo_name_id: Unique ID github has assigned the project
    :param git_hash: The git hash of the deployed code
    :param url: The url builder has deployed this project to
    :param path: The path of the site on the static server
    :param oauth_token: Token used to access the project on github
    :param status: The current status of the deployed version on Franklin
    """

    REGISTERED = 'REG'
    BUILDING = 'BLD'
    SUCCESS = 'SUC'
    FAILED = 'FAL'

    STATUS_CHOICES = (
        (REGISTERED, 'Webhook Registered'),
        (BUILDING, 'Building Now'),
        (SUCCESS, 'Deploy Succeeded'),
        (FAILED, 'Deploy Failed')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.CharField(max_length=100, default='')
    owner_id = models.PositiveIntegerField(blank=True, null=True)
    repo_name = models.CharField(max_length=100)
    repo_name_id = models.PositiveIntegerField(blank=True, null=True)
    git_hash = models.CharField(max_length=40)
    url = models.CharField(max_length=100, default='', db_index=True)
    path = models.CharField(max_length=100)
    oauth_token = models.CharField(max_length=255, default='')
    status = models.CharField(
        max_length=3, choices=STATUS_CHOICES, default=REGISTERED)

    def is_deployable_event(self, github_event):
        # TODO - add logic here to compare data from the github webhook event
        # with what we already have in the DB about acceptable deploy events.
        # e.g. Only if branch 'release' and has a tag formatted 'v ##.##.##'
        return True

    def build(self):
        url = os.environ['BUILDER_URL']
        headers = {'content-type': 'application/json'}
        body = {
                    "github_token": self.oauth_token,
                    "git_hash": self.git_hash,
                    "repo_owner": self.owner,
                    "path": self.path,
                    "repo_name": self.repo_name
                }
        r = None
        try:
            r = requests.post(url, data=json.dumps(body), headers=headers)
        except (ConnectionError, HTTPError, Timeout) as e:
            logger.error('Connection exception : %s', e)
        except:
            logger.error('Unexpected Builder error: %s', sys.exc_info()[0])

        if r is not None:
            if (status.is_success(r.status_code) and 
                    r.headers['Content-Type'] == 'application/json'):
                building_status = r.json()['building']
                if building_status:
                    self.status = self.BUILDING
                    self.save()
                    return
                else:
                    logger.error("Negative response from Builder")
            else:
                logger.error('Builder responded without json')
        else:
            logger.error('Bad response from builder.')
        self.status = self.FAILED
        self.save()

    def save(self, *args, **kwargs):
        base_path = os.environ['BASE_PROJECT_PATH']
        self.path = "{0}/{1}/{2}".format(base_path, self.owner, self.repo_name)
        self.url = "{0}.{1}".format(self.repo_name, os.environ['BASE_URL'])
        super(Site, self).save(*args, **kwargs)

    def __str__(self):
        return self.repo_name
