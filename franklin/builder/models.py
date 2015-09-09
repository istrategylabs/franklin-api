import logging
import requests
import json
import os
import uuid

from django.db import models

logger = logging.getLogger(__name__)


class Site(models.Model):
    """ Represents a 'deployed' or soon-to-be deployed static site.

    :param id: A unique site identified
    :param repo_name: The full repo name of project on github
    :param git_hash: The git hash of the deployed code
    :param path: The path of the site on the static server
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repo_name = models.CharField(max_length=100)
    git_hash = models.CharField(max_length=40)
    url = models.CharField(max_length=100, default='', db_index=True)
    path = models.CharField(max_length=100)

    def build(self):
        url = os.environ['BUILDER_URL']
        repo_owner = self.repo_name.split("/")[0]
        repo_name = self.repo_name.split("/")[1]
        headers = {'content-type': 'application/json'}
        body = {
                    "git_hash": self.git_hash,
                    "repo_owner": repo_owner,
                    "path": self.path,
                    "repo_name": repo_name
                }
        try:
            r = requests.post(url, data=json.dumps(body), headers=headers)
            response = r.json()['building']
            if not response:
                logger.error("Builder says its not building")
            print('Response HTTP Status Code   : {status_code}'.format(
                status_code=r.status_code))
            print('Response HTTP Response Body : {content}'.format(
                content=r.content))
        except requests.exceptions.RequestException as e:
            logger.error("Failed to call build api")

    def save(self, *args, **kwargs):
        base_path = os.environ['BASE_PROJECT_PATH']
        self.path = "{0}/{1}".format(base_path, self.repo_name)
        if not self.url:
            self.url = "{0}.{1}".format(
                self.repo_name.replace('/', '-'),
                os.environ['BASE_URL']
            )
        super(Site, self).save(*args, **kwargs)
        self.build()

    def __str__(self):
        return self.repo_name
