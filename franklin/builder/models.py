import json
import logging
import os
import re
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import sys
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from rest_framework import status

logger = logging.getLogger(__name__)

class Owner(models.Model):
    """ Represents a github user or organization that owns repos

    :param name: The unique name for this user or org (taken from github)
    :param github_id: Unique ID github has assigned the owner
    """
    name = models.CharField(max_length=100)
    github_id = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta(object):
        verbose_name = _('Owner')
        verbose_name_plural = _('Owners')


class Site(models.Model):
    """ Represents a 'deployed' or soon-to-be deployed static site.

    :param owner: Ref to the owner of the project
    :param name: The name of the project on github
    :param github_id: Unique ID github has assigned the project
    :param deploy_key: Token used to access the project on github
    """

    DEFAULT_ENV = 'Production'

    owner = models.ForeignKey(Owner, related_name='sites')
    name = models.CharField(max_length=100)
    github_id = models.PositiveIntegerField(unique=True)
    deploy_key = models.CharField(max_length=255, default='')

    def get_deployable_event(self, github_event):
        git_hash = github_event.get_event_hash()
        event = github_event.get_change_location()
        is_tag_event = github_event.is_tag_event()

        env_to_deploy = None
        for env in self.environments.all():
            if env.deploy_type == Environment.BRANCH and env.branch in event:
                env_to_deploy = env
            elif (env.deploy_type == Environment.TAG and is_tag_event 
                and re.match(env.tag_regex, event)):
                env_to_deploy = env
                
        if env_to_deploy and git_hash:
            build, created = env.past_builds.get_or_create(
                git_hash=git_hash, site=self)
            if build:
                env.current_deploy = build
                env.save()
                return env_to_deploy
        return None
    
    def save(self, *args, **kwargs):
        super(Site, self).save(*args, **kwargs)
        if not self.environments.exists():
            self.environments.create(name=self.DEFAULT_ENV)

    def __str__(self):
        return self.name
    
    class Meta(object):
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')


class Build(models.Model):
    """ Represents built code that has been deployed to a folder. This build
    can be referenced by the HTTP server for routing

    :param site: Reference to the project for this build instance
    :param git_hash: The git hash of the deployed code
    :param created: Date this code was built
    :param path: The path of the site on the static server
    """

    site = models.ForeignKey(Site, related_name='builds')
    git_hash = models.CharField(max_length=40)
    created = models.DateTimeField(editable=False)
    path = models.CharField(max_length=100)
    
    def save(self, *args, **kwargs):
        base_path = os.environ['BASE_PROJECT_PATH']
        self.path = "{0}/{1}/{2}/{3}".format(base_path, 
                                             self.site.owner.name, 
                                             self.site.name,
                                             self.git_hash)
        if not self.id:
            self.created = timezone.now()
        super(Build, self).save(*args, **kwargs)
    
    def __str__(self):
        return '%s %s' % (self.site.name, self.git_hash)
    
    class Meta(object):
        verbose_name = _('Build')
        verbose_name_plural = _('Builds')


class Environment(models.Model):
    """ Represents the configuration for a specific deployed environment

    :param site: Ref to the project this environment is hosting
    :param name: Name for the environment.
    :param description: Optional detailed information about the environment
    :param deploy_type: What event will trigger a build. (push to branch,
                        tagging a commit, or manually by an admin user)
    :param branch: Code branch that is used for deploying
    :param tag_regex: Tag events matching this regular expression will be
                      deployed (If deploy_type is tag)
    :param url: The url builder has deployed this project to
    :param current_deployed: Ref to the current build of code
    :param past_builds: Ref to all builds that can be marked current_deployed
    :param status: The current status of the deployed version on Franklin
    """
    
    BRANCH = 'BCH'
    TAG = 'TAG'
    PROMOTE = 'PRO'

    DEPLOY_CHOICES = (
        (BRANCH, 'Any push to a branch'),
        (TAG, 'Any commit matching a tag regex'),
        (PROMOTE, 'Manually from a lower environment')
    )
    
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
    
    site = models.ForeignKey(Site, related_name='environments')
    name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=20480, default='', blank=True)
    deploy_type = models.CharField(
        max_length=3, choices=DEPLOY_CHOICES, default=BRANCH)
    branch = models.CharField(max_length=100, default='master')
    tag_regex = models.CharField(max_length=100, blank=True)
    url = models.CharField(
        max_length=100, default='', db_index=True, blank=True)
    current_deploy = models.ForeignKey(
        Build, related_name='deployments', null=True, blank=True)
    past_builds = models.ManyToManyField(
        Build, related_name='environments', blank=True)
    status = models.CharField(
        max_length=3, choices=STATUS_CHOICES, default=REGISTERED)
    
    def build(self):
        url = os.environ['BUILDER_URL']
        headers = {'content-type': 'application/json'}
        body = {
                    "github_token": self.site.deploy_key,
                    "git_hash": self.current_deploy.git_hash,
                    "repo_owner": self.site.owner.name,
                    "path": self.current_deploy.path,
                    "repo_name": self.site.name
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
        if self.current_deploy:
            if self.name == self.site.DEFAULT_ENV:
                self.url = "{0}.{1}".format(self.site.name, 
                                            os.environ['BASE_URL'])
            else:
                self.url = "{0}-{1}.{2}".format(self.site.name, 
                                                self.name, 
                                                os.environ['BASE_URL'])
        super(Environment, self).save(*args, **kwargs)
    
    def __str__(self):
        return '%s %s' % (self.site.name, self.name)

    class Meta(object):
        verbose_name = _('Environment')
        verbose_name_plural = _('Environments')
        unique_together = ('name', 'site')
