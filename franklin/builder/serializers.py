import os

from rest_framework import serializers

from builder.models import Owner, Site


class OwnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Owner
        fields = ('name', 'github_id')


class SiteSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    
    class Meta:
        model = Site
        fields = ('name', 'github_id', 'owner')

    def create(self, validated_data):
        owner_data = validated_data.pop('owner')
        owner = Owner.objects.create(**owner_data)
        site = Site.objects.create(owner=owner, 
                                   deploy_key=os.environ['GITHUB_OAUTH'], 
                                   **validated_data)
        return site

    # TODO - Need def for Update??
