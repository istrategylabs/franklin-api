import logging
from django.conf import settings
from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _

from builder.models import Site
from github.api import get_user_orgs

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
        # Return all sites owned by the user or one of their org memberships.

        # Init the owners list with the current user as they are an owner
        owners = [int(self.user.social_auth.get(provider='github').uid)]
        orgs = get_user_orgs(self.user)
        for org in orgs:
            owners.append(org.get('id', ''))
        return Site.objects.filter(owner__github_id__in=owners)\
                           .filter(is_active=True).all()

    def update_repos_for_user(self, repos):
        # Clear out the users sites in case permissions have changed
        self.sites.clear()
        all_sites = Site.objects.all()
        for repo in repos:
            site = all_sites.filter(github_id=repo['id']).first()
            if site and repo['permissions']['admin'] == True:
                self.sites.add(site)
        return self.sites.all()

    def __str__(self):
        return self.user.username

    class Meta(object):
        verbose_name = _('Detail')
        verbose_name_plural = _('Details')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_details_for_new_user(sender, created, instance, **kwargs):
    if created:
        UserDetails.objects.create(user=instance)
