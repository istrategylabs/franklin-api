from rest_framework import serializers

from builder.models import Build, BranchBuild, Environment, Owner, Site, \
        TagBuild


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
    class Meta:
        model = BranchBuild
        fields = ('branch', 'git_hash')


class TagBuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagBuild
        fields = ('tag')


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ('name', 'url', 'status')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class EnvironmentDetailSerializer(serializers.ModelSerializer):

    def to_representation(self, data):
        current_deploy = data.current_deploy
        build_result = {}
        if not current_deploy:
            if self.context and self.context.get('user', None):
                user = self.context['user']
                branch, git_hash = data.site.get_newest_commit(user)
                build_result = {
                        'default_branch': branch,
                        'git_hash': git_hash
                }
        elif hasattr(current_deploy, 'branchbuild'):
            build = BranchBuild.objects.get(created=current_deploy.created)
            serializer = BranchBuildSerializer(build)
            build_result = serializer.data
        elif hasattr(current_deploy, 'tagbuild'):
            build = TagBuild.objects.get(created=current_deploy.created)
            serializer = TagBuildSerializer(build)
            build_result = serializer.data

        env_serializer = EnvironmentSerializer(data)
        result = env_serializer.data
        result['current_deploy'] = build_result
        return result

    class Meta:
        model = Environment
        fields = ('name', 'url', 'status', 'current_deploy')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class EnvironmentStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Environment
        fields = ('status',)


class SiteSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    environments = EnvironmentDetailSerializer(many=True, required=False)

    class Meta:
        model = Site
        fields = ('name', 'github_id', 'owner', 'environments', 'is_active')
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
        fields = ('name', 'github_id', 'owner', 'is_active')


class FlatSiteSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        env = data.get_default_environment()
        site_serializer = SiteOnlySerializer(data)
        default_env_serializer = EnvironmentStatusSerializer(env)
        result = site_serializer.data
        result['default_environment'] = default_env_serializer.data
        return result
