import os
import uuid

from django.db import models


class Site(models.Model):
    """ Represents a 'deployed' or soon-to-be deployed static site.

    :param id: A unique site identified
    :param git_hash: The git hash of the deployed code
    :param path: The path of the site on the static server
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    git_hash = models.CharField(max_length=50)
    path = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        base_path = os.environ['BASE_PROJECT_PATH']
        self.path = "{0}/{1}".format(base_path, self.id)
        super(Site, self).save(*args, **kwargs)
