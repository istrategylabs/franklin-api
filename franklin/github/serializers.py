from rest_framework import serializers

from builder.models import Site


class HeadCommitSerializer(serializers.Serializer):
    id = serializers.CharField(min_length=40, max_length=40)
    # Also available
    # message, timestamp, url, author{}, committer{}, ...
    
class RepositorySerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    id = serializers.IntegerField()
    # Also available
    # name, owner{}, html_url, fork, url, master_branch, ...

class GithubWebhookSerializer(serializers.Serializer):
    head_commit = HeadCommitSerializer()
    repository = RepositorySerializer()

    # TODO - We may want to do an update instead of a create
    # We may want to do creation as a separate setup step for new projects.
    # That would have us auto-configuring webhooks by making secure calls to
    # github during our setup step.
    # https://developer.github.com/v3/repos/hooks/#create-a-hook
    def create(self, validated_data):
        repo_id = validated_data.pop('repository').get('id')
        git_hash = validated_data.pop('head_commit').get('id')
        site, created = Site.objects.get_or_create(repo_name_id=repo_id)
        site.git_hash = git_hash
        site.save()
        return site
