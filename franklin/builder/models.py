import logging
import os
import re
import uuid

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

from core.exceptions import ServiceUnavailable
from core.helpers import generate_ssh_keys, make_rest_post_call
from github.api import get_branch_details, get_default_branch


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
    :param deploy_key_id: The id in Github's DB for the key they have stored
    :param webhook_id: The id in Github's DB for the webhook they have stored
    :param is_active: If False, means the site is marked for deletion
    """
    DEFAULT_ENV = _('Production')

    owner = models.ForeignKey(Owner, related_name='sites')
    name = models.CharField(max_length=100)
    github_id = models.PositiveIntegerField(unique=True)
    deploy_key = models.TextField(blank=True, null=True)
    deploy_key_secret = models.TextField(blank=True, null=True)
    deploy_key_id = models.CharField(blank=True, null=True, max_length=12)
    webhook_id = models.CharField(blank=True, null=True, max_length=12)
    is_active = models.BooleanField(default=True)

    def get_deployable_environment(self, event, is_tag_event=False):
        if self.is_active:
            for env in self.environments.all():
                if (env.deploy_type == Environment.BRANCH and not
                        is_tag_event and event.endswith(env.branch)):
                    return env
                elif (env.deploy_type == Environment.TAG and
                        is_tag_event and re.match(env.tag_regex, event)):
                    return env
        return None

    def get_newest_commit(self, user):
        """ Calls github and retrieves the current git hash of the most recent
        code push to the default branch of the repo
        """
        branch = get_default_branch(self, user)
        git_hash = get_branch_details(self, user, branch)
        return (branch, git_hash)

    def get_most_recent_build(self):
        return BranchBuild.objects.filter(site=self)\
                                  .order_by('-created').first()

    def save(self, user=None, *args, **kwargs):
        if not self.deploy_key:
            self.deploy_key, self.deploy_key_secret = generate_ssh_keys()
        if not self.environments.exists() and user:
            branch = get_default_branch(self, user)
            self.environments.create(
                name=self.DEFAULT_ENV, deploy_type=Environment.PROMOTE)
            self.environments.create(name='Staging', branch=branch)
        super(Site, self).save(*args, **kwargs)

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
    :param deployed: Date this code was last deployed to an environment
    :param path: The path of the site on the static server
    """

    NEW = 'NEW'
    BUILDING = 'BLD'
    SUCCESS = 'SUC'
    FAILED = 'FAL'
    STATUS_CHOICES = (
        (NEW, _('new')),
        (BUILDING, _('building')),
        (SUCCESS, _('success')),
        (FAILED, _('failed'))
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, related_name='builds')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES,
                              default=NEW)

    @property
    def path(self):
        return "{0}/{1}".format(self.site.github_id, self.uuid)

    def can_build(self):
        return self.status is not self.BUILDING

    def deploy(self, environment):
        if self.can_build():
            callback = os.environ['API_BASE_URL'] + \
                reverse('webhook:builder', args=[str(self.uuid), ])

            url = os.environ['BUILDER_URL'] + '/build'
            headers = {'content-type': 'application/json'}
            body = {
                "deploy_key": self.site.deploy_key_secret,
                "branch": self.branch,
                "git_hash": self.git_hash,
                "repo_owner": self.site.owner.name,
                "path": self.path,
                "repo_name": self.site.name,
                "environment": environment.name.lower(),
                'callback': callback
            }
            try:
                make_rest_post_call(url, headers, body)
            except:
                logger.warn('Builder down?')
                msg = 'Service temporarily unavailable: franklin-build'
                raise ServiceUnavailable(detail=msg)
            self.status = self.BUILDING
            self.save()
        else:
            logger.error("Build being/been built by builder...")

    def __str__(self):
        return '%s - %s' % (self.status, self.created)


class BranchBuild(Build):
    """ Flavor of build that was created from a branch

    :param branch: If a branch build, the name of the branch
    :param git_hash: If a branch build, the git hash of the deployed code
    """
    git_hash = models.CharField(max_length=40)
    branch = models.CharField(max_length=100)

    def __str__(self):
        return '%s %s' % (self.site.name, self.uuid)

    class Meta(object):
        verbose_name = _('Branch Build')
        verbose_name_plural = _('Branch Builds')


class Environment(models.Model):
    """ Represents the configuration for a specific deployed environment

    :param site: Ref to the project this environment is hosting
    :param name: Name for the environment.
    :param deploy_type: What event will trigger a build. (push to branch,
                        tagging a commit, or manually by an admin user)
    :param branch: Code branch that is used for deploying
    :param tag_regex: Tag events matching this regular expression will be
                      deployed (If deploy_type is tag)
    :param url: The url builder has deployed this project to
    :param past_builds: Ref to all builds that can be marked current_deployed
    :param status: The current status of the deployed version on Franklin
    """

    BRANCH = 'BCH'
    TAG = 'TAG'
    PROMOTE = 'PRO'
    DEPLOY_CHOICES = (
        (BRANCH, _('branch')),
        (TAG, _('tag')),
        (PROMOTE, _('promote'))
    )

    site = models.ForeignKey(Site, related_name='environments')
    name = models.CharField(max_length=100, default='')
    deploy_type = models.CharField(
        max_length=3, choices=DEPLOY_CHOICES, default=BRANCH)
    branch = models.CharField(max_length=100, default='master')
    tag_regex = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=100, unique=True)
    past_builds = models.ManyToManyField(
        Build, related_name='environments', through='Deploy', blank=True)

    def get_current_deploy(self):
        return self.past_builds.filter(status=Build.SUCCESS)\
                               .order_by('-created').first()

    def save(self, *args, **kwargs):
        if not self.url:
            if self.name == self.site.DEFAULT_ENV:
                self.url = "{0}.{1}".format(self.site.name.lower(),
                                            os.environ['BASE_URL'])
            else:
                self.url = "{0}-{1}.{2}".format(self.site.name.lower(),
                                                self.name.lower(),
                                                os.environ['BASE_URL'])
        super(Environment, self).save(*args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.site.name, self.name)

    class Meta(object):
        verbose_name = _('Environment')
        verbose_name_plural = _('Environments')
        unique_together = ('name', 'site')


class Deploy(models.Model):
    """ A deployment event; represented as a link between an environment and a
    build object.

    :param environment: link to environment
    :param build: link to build
    :param deployed: Date this code was last deployed to an environment
    """
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    build = models.ForeignKey(Build, on_delete=models.CASCADE)
    deployed = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return '%s %s' % (self.environment.site.name, self.deployed)
