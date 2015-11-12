from rest_framework import serializers

from builder.models import Owner, Site


class OwnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Owner
        fields = ('name', 'github_id')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class SiteSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()

    class Meta:
        model = Site
        fields = ('name', 'github_id', 'owner')
        # Not ideal, but you can't update existing models without disabling
        # validation for our unique=True github_id
        # This is a known issue in DRF:
        #   https://github.com/tomchristie/django-rest-framework/issues/2996
        #   https://groups.google.com/d/msg/django-rest-framework/W6F9_IJiZrY/6gDa_GmhcasJ
        # If this is fixed, add update() and rewrite create() to be more like:
        #   Site.objects.create(owner=owner, **validated_data)
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }

    def create(self, validated_data):
        owner_data = validated_data.pop('owner')
        owner_id = owner_data.get('github_id', None)
        repo_id = validated_data.get('github_id', None)
        if owner_id and repo_id:
            owner, o_created = Owner.objects.update_or_create(
                github_id=owner_id, defaults=owner_data)
            if owner:
                site, s_created = Site.objects.update_or_create(
                    github_id=repo_id, owner=owner, defaults=validated_data)
                if site:
                    return site
        return None
