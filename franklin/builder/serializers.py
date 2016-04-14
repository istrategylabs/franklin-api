from rest_framework import serializers

from builder.models import BranchBuild, Environment, Owner, Site


class OwnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Owner
        fields = ('name', 'github_id')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class BranchBuildSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        result = super(BranchBuildSerializer, self).to_representation(instance)
        result['status'] = instance.get_status_display()
        if self.context and self.context.get('env', None):
            deploy = instance.deploy_set\
                             .filter(environment=self.context['env'])\
                             .first()
            if deploy:
                result['deployed'] = deploy.deployed
        return result

    class Meta:
        model = BranchBuild
        fields = ('branch', 'git_hash', 'status', 'created')


class EnvironmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Environment
        fields = ('name', 'url')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class EnvironmentDetailSerializer(serializers.Serializer):

    def to_representation(self, instance):
        env_serializer = EnvironmentSerializer(instance)
        result = env_serializer.data
        current_deploy = instance.get_current_deploy()
        result['build'] = {}
        if current_deploy and hasattr(current_deploy, 'branchbuild'):
            build = BranchBuild.objects.get(created=current_deploy.created)
            serializer = BranchBuildSerializer(
                build, context={'env': instance})
            result['build'] = serializer.data
        return result


class SiteSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    environments = EnvironmentDetailSerializer(many=True, required=False)

    def to_representation(self, instance):
        result = super(SiteSerializer, self).to_representation(instance)
        if self.context and self.context.get('user', None):
            user = self.context['user']
            branch, git_hash = instance.get_newest_commit(user)
            result['default_branch'] = branch
        build = instance.get_most_recent_build()
        if build:
            latest_build_serializer = BranchBuildSerializer(build)
        result['build'] = latest_build_serializer.data if build else {}
        return result

    class Meta:
        model = Site
        fields = ('name', 'github_id', 'owner', 'environments')
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


class SiteOnlySerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()

    class Meta:
        model = Site
        fields = ('name', 'github_id', 'owner')


class FlatSiteSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        site_serializer = SiteOnlySerializer(data)
        result = site_serializer.data
        build = data.get_most_recent_build()
        if build:
            latest_build_serializer = BranchBuildSerializer(build)
        result['build'] = latest_build_serializer.data if build else {}
        return result
