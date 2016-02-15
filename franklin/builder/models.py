import logging
import os
import re

from django.db import models
from django.utils.translation import ugettext as _

from rest_framework import status

from core.helpers import generate_ssh_keys, make_rest_post_call

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
    :param deploy_key_secret: Secret portion of the deploy_key
    """
    DEFAULT_ENV = _('Production')

    owner = models.ForeignKey(Owner, related_name='sites')
    name = models.CharField(max_length=100)
    github_id = models.PositiveIntegerField(unique=True)
    deploy_key = models.TextField(blank=True, null=True)
    deploy_key_secret = models.TextField(blank=True, null=True)

    def get_deployable_event(self, github_event):
        git_hash = github_event.get_event_hash()
        event = github_event.get_change_location()
        is_tag_event = github_event.is_tag_event()

        build = None
        for env in self.environments.all():
            if (env.deploy_type == Environment.BRANCH and not
                    is_tag_event and event.endswith(env.branch)):
                build, created = BranchBuild.objects.get_or_create(
                    git_hash=git_hash, branch=env.branch, site=self)
            elif (env.deploy_type == Environment.TAG and
                    is_tag_event and re.match(env.tag_regex, event)):
                build, created = TagBuild.objects.get_or_create(
                    tag=event, site=self)

            if build:
                env.current_deploy = build
                env.save()
                return env
        return None

    def save(self, *args, **kwargs):
        if not self.deploy_key:
            self.deploy_key, self.deploy_key_secret = generate_ssh_keys()
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
    :param git_hash: If a branch build, the git hash of the deployed code
    :param created: Date this code was built
    :param path: The path of the site on the static server
    """

    site = models.ForeignKey(Site, related_name='builds')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    path = models.CharField(max_length=100, blank=True)

    def get_path(self, site, name):
        return "{0}/{1}".format(site, name)


class TagBuild(Build):
    """ Flavor of build that was created from a tag

    :param tag: If a tag build, the name of the tag
    """
    tag = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        clean_tag = re.sub('[^a-zA-Z0-9]', '', self.tag)
        self.path = self.get_path(self.site.github_id, clean_tag)
        super(TagBuild, self).save(*args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.site.name, self.tag)

    class Meta(object):
        verbose_name = _('Tag Build')
        verbose_name_plural = _('Tag Builds')


class BranchBuild(Build):
    """ Flavor of build that was created from a branch

    :param branch: If a branch build, the name of the branch
    :param git_hash: If a branch build, the git hash of the deployed code
    """
    git_hash = models.CharField(max_length=40)
    branch = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.path = self.get_path(self.site.github_id, self.git_hash)
        super(BranchBuild, self).save(*args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.site.name, self.git_hash)

    class Meta(object):
        verbose_name = _('Branch Build')
        verbose_name_plural = _('Branch Builds')
        unique_together = ('git_hash', 'branch')


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
        (BRANCH, _('Any push to a branch')),
        (TAG, _('Any commit matching a tag regex')),
        (PROMOTE, _('Manually from a lower environment'))
    )

    REGISTERED = 'REG'
    BUILDING = 'BLD'
    SUCCESS = 'SUC'
    FAILED = 'FAL'

    STATUS_CHOICES = (
        (REGISTERED, _('Webhook Registered')),
        (BUILDING, _('Building Now')),
        (SUCCESS, _('Deploy Succeeded')),
        (FAILED, _('Deploy Failed'))
    )

    site = models.ForeignKey(Site, related_name='environments')
    name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=20480, default='', blank=True)
    deploy_type = models.CharField(
        max_length=3, choices=DEPLOY_CHOICES, default=BRANCH)
    branch = models.CharField(max_length=100, default='master')
    tag_regex = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=100, unique=True)
    current_deploy = models.ForeignKey(
        Build, related_name='deployments', null=True, blank=True)
    past_builds = models.ManyToManyField(
        Build, related_name='environments', blank=True)
    status = models.CharField(
        max_length=3, choices=STATUS_CHOICES, default=REGISTERED)

    def build(self):
        if self.current_deploy:
            is_tag_build = hasattr(self.current_deploy, 'tagbuild')
            branch = self.current_deploy.branch if not is_tag_build else ''
            tag = self.current_deploy.tag if is_tag_build else ''
            git_hash = self.current_deploy.git_hash if not is_tag_build else ''

            url = os.environ['BUILDER_URL'] + '/build'
            headers = {'content-type': 'application/json'}
            body = {
                "deploy_key": self.site.deploy_key,
                "branch": branch,
                "tag": tag,
                "git_hash": git_hash,
                "repo_owner": self.site.owner.name,
                "path": self.current_deploy.path,
                "repo_name": self.site.name,
                "environment_id": self.id
                }

            response = make_rest_post_call(url, headers, body)
            if not status.is_success(response.status_code):
                logger.error("Negative response from Builder: %s",
                             response.status_code)
                self.status = self.FAILED
            else:
                self.status = self.BUILDING
            self.save()

    def save(self, *args, **kwargs):
        if not self.url:
            if self.name == self.site.DEFAULT_ENV:
                self.url = "{0}.{1}".format(self.site.name.lower(),
                                            os.environ['BASE_URL'])
            else:
                self.url = "{0}-{1}.{2}".format(self.site.name.lower(),
                                                self.name.lower(),
                                                os.environ['BASE_URL'])
        if (self.current_deploy and not
                self.past_builds.filter(pk=self.current_deploy.pk).exists()):
            self.past_builds.add(self.current_deploy)
        super(Environment, self).save(*args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.site.name, self.name)

    class Meta(object):
        verbose_name = _('Environment')
        verbose_name_plural = _('Environments')
        unique_together = ('name', 'site')
