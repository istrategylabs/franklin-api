import logging
from rest_framework import serializers

from builder.models import BranchBuild, Owner, Site

logger = logging.getLogger(__name__)


class HeadCommitSerializer(serializers.Serializer):
    id = serializers.CharField(min_length=40, max_length=40)
    # Also available
    # message, timestamp, url, author{}, committer{}, ...


class OwnerSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    login = serializers.CharField(required=False)


class RepositorySerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    id = serializers.IntegerField()
    owner = OwnerSerializer()
    html_url = serializers.CharField()
    # Also available
    # name, html_url, fork, url, master_branch, ...

    def create(self, validated_data):
        owner_data = validated_data.pop('owner')
        owner_id = owner_data.get('id', None)
        repo_id = validated_data.get('id', None)
        if owner_id and repo_id:
            owner, o_created = Owner.objects.update_or_create(
                    github_id=owner_id, defaults={'name': owner_data['login']})
            if owner:
                site, s_created = Site.objects.update_or_create(
                        github_id=repo_id, owner=owner,
                        defaults={'name': validated_data['name']})
                if site:
                    return site
        return None


class GithubWebhookSerializer(serializers.Serializer):
    head_commit = HeadCommitSerializer()
    repository = RepositorySerializer()
    ref = serializers.CharField(max_length=100)
    ref_type = serializers.CharField(max_length=100, required=False)

    def get_existing_site(self):
        if self.is_valid():
            repo_id = self.validated_data.pop('repository').get('id')
            try:
                return Site.objects.get(github_id=repo_id)
            except Site.DoesNotExist:
                logger.error("Cannot deploy %s: doesn't exist", str(repo_id))
        return None

    def is_tag_event(self):
        if self.validated_data:
            ref_type = self.validated_data.get('ref_type', None)
            if ref_type and ref_type == 'tag':
                return True
        return False

    def get_event_hash(self):
        if self.validated_data:
            head_commit = self.validated_data.get('head_commit', None)
            if head_commit:
                git_hash = head_commit.get('id', None)
                return git_hash
        return None

    def get_change_location(self):
        if self.validated_data:
            # Depending on the event, 'ref' will contain the name of the branch
            # code was push to, or the name of the created tag
            return self.validated_data.get('ref', None)
        return None

    def create_build_and_deploy(self):
        site = self.get_existing_site()
        git_hash = self.get_event_hash()
        environment = site.get_deployable_environment(
            self.get_change_location(), git_hash, self.is_tag_event())
        if environment:
            build, created = BranchBuild.objects.create(
                git_hash=git_hash, site=site)
            build.deploy(environment)
