import logging
from django.conf import settings
from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _

from builder.models import Site
from core.helpers import make_rest_get_call

github_base = 'https://api.github.com/'
logger = logging.getLogger(__name__)


class UserDetails(models.Model):
    """ Extra details and functions attached to the default user created with
    github social signin

    :param user: FK to a unique user
    :param sites: List of sites the user has permission to deploy
    """
    user = models.OneToOneField(
            settings.AUTH_USER_MODEL, related_name='details')
    sites = models.ManyToManyField(Site, related_name='admins')

    def get_user_repos(self):
        social = self.user.social_auth.get(provider='github')
        token = social.extra_data['access_token']
        have_next_page = True
        url = github_base + 'user/repos?per_page=100'
        # TODO - Confirm that a header token is the best/most secure way to go
        headers = {
                    'content-type': 'application/json',
                    'Authorization': 'token ' + token
                  }
        repos = []

        while have_next_page:
            response = None
            have_next_page = False  # when in doubt, leave the loop after 1
            response = make_rest_get_call(url, headers)

            if response is not None:
                # Add all of the repos to our list
                for repo in response.json():
                    repo_data = {}
                    repo_data['id'] = repo['id']
                    repo_data['name'] = repo['name']
                    repo_data['url'] = repo['html_url']
                    repo_data['owner'] = {}
                    repo_data['owner']['name'] = repo['owner']['login']
                    repo_data['owner']['id'] = repo['owner']['id']
                    repo_data['permissions'] = {}
                    repo_data['permissions']['admin'] = repo['permissions']['admin']
                    repos.append(repo_data)

                # If the header has a paging link called 'next', update our url
                # and continue with the while loop
                if response.links and response.links.get('next', None):
                    url = response.links['next']['url']
                    have_next_page = True

        if not repos:
            logger.error('Failed to find repos for user', self.user.username)
        return repos

    def update_repos_for_user(self, repos):
        # Clear out the users sites in case permissions have changed
        self.sites.clear()
        all_sites = Site.objects.all()
        for repo in repos:
            site = all_sites.filter(github_id=repo['id']).first()
            if site and repo['permissions']['admin'] == True:
                self.sites.add(site)
        return self.sites.all()

    def has_repo_access(self, site):
        if self.sites.count() == 0 or site not in self.sites.all():
            repos = self.get_user_repos()
            self.update_repos_for_user(repos)
        if site in self.sites.all():
            return True
        return False

    def __str__(self):
        return self.user.username

    class Meta(object):
        verbose_name = _('Detail')
        verbose_name_plural = _('Details')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_details_for_new_user(sender, created, instance, **kwargs):
    if created:
        UserDetails.objects.create(user=instance)
