import os

from rest_framework import serializers

from builder.models import Site


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('owner', 'owner_id', 'repo_name', 'repo_name_id')

    def save(self):
        repo_id = self.validated_data.get('repo_name_id', None)
        site, created = Site.objects.get_or_create(repo_name_id=repo_id)
        if site:
            site.owner = self.validated_data.get('owner', site.owner)
            site.owner_id = self.validated_data.get('owner_id', site.owner_id)
            site.repo_name = self.validated_data.get('repo_name', site.repo_name)
            site.oauth_token = os.environ['GITHUB_OAUTH']
            site.save()
            return site
        return None
