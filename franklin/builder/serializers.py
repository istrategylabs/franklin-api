from rest_framework import serializers

from builder.models import BranchBuild, Environment, Owner, Site, TagBuild


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
        fields = ('branch', 'git_hash', 'created')


class TagBuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagBuild
        fields = ('tag', 'created')


class EnvironmentSerializer(serializers.ModelSerializer):

    def to_representation(self, data):
        return {
            'name': data.name,
            'url': data.url,
            'status': data.get_status_display(),
            'deploy_type': data.get_deploy_type_display()
        }

    class Meta:
        model = Environment
        fields = ('name', 'url', 'status', 'deploy_type')
        extra_kwargs = {
            "github_id": {
                "validators": [],
            },
        }


class EnvironmentDetailSerializer(serializers.Serializer):

    def to_representation(self, data):
        current_deploy = data.current_deploy
        deploy_type = data.deploy_type
        build_result = {}
        default_branch_details = {}
        env_serializer = EnvironmentSerializer(data)
        result = env_serializer.data
        if deploy_type != Environment.PROMOTE:
            if not current_deploy:
                if self.context and self.context.get('user', None):
                    user = self.context['user']
                    branch, git_hash = data.site.get_newest_commit(user)
                    default_branch_details = {
                            'branch': branch,
                            'git_hash': git_hash
                    }
            else:
                if hasattr(current_deploy, 'branchbuild'):
                    build = BranchBuild.objects.get(
                                created=current_deploy.created)
                    serializer = BranchBuildSerializer(build)
                    build_result = serializer.data
                elif hasattr(current_deploy, 'tagbuild'):
                    build = TagBuild.objects.get(
                                created=current_deploy.created)
                    serializer = TagBuildSerializer(build)
                    build_result = serializer.data

        result['current_deploy'] = build_result
        result['default_branch'] = default_branch_details
        return result


class EnvironmentStatusSerializer(serializers.ModelSerializer):

    def to_representation(self, data):
        return {
            'status': data.get_status_display(),
        }

    class Meta:
        model = Environment
        fields = ('status',)


class SiteSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer()
    environments = EnvironmentDetailSerializer(many=True, required=False)

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
        build = BranchBuild.objects.filter(site=data)\
                                   .order_by('-created').first()
        site_serializer = SiteOnlySerializer(data)
        result = site_serializer.data
        result['build'] = {}
        if build:
            latest_build_serializer = BranchBuildSerializer(build)
            result['build'] = latest_build_serializer.data
        return result
