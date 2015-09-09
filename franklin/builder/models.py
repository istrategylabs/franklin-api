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
        r = None
        try:
            r = requests.post(url, data=json.dumps(body), headers=headers)
        except (ConnectionError, HTTPError, Timeout) as e:
            logger.error('Response HTTP Status Code   : %s', e.status_code)
            logger.error('Response HTTP Response Body : %s', e.content)
        except:
            logger.error('Unexpected Builder error: %s', sys.exc_info()[0])

        if r is not None:
            if (r.status_code == requests.codes.ok and 
                    r.headers['Content-Type'] == 'application/json'):
                building_status = r.json()['building']
                if not building_status:
                    logger.error("Negative response from Builder")
                # TODO - Update the DB with builder's status. There should beFive 
                # states should be: 'STARTING', 'BUILDING', 'NOT BUILDING', 
                # 'DEPLOY SUCCESS', and 'DEPLOY FAILED'
            else:
                logger.error('Builder responsed without json')
        else:
            logger.error('Bad response from builder.')

    def save(self, *args, **kwargs):
        base_path = os.environ['BASE_PROJECT_PATH']
        self.path = "{0}/{1}".format(base_path, self.repo_name)
        if not self.url:
            repo_name = self.repo_name.split("/")[1]
            self.url = "{0}.{1}".format(
                repo_name,
                os.environ['BASE_URL']
            )
        super(Site, self).save(*args, **kwargs)

        # This line helps with testing. We will remove once we add mocking.
        if os.environ['ENV'] is not 'test':
            self.build()

    def __str__(self):
        return self.repo_name
