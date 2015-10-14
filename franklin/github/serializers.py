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

    def get_existing_site(self):
        if self.is_valid():
            repo_id = self.validated_data.pop('repository').get('id')
            git_hash = self.validated_data.pop('head_commit').get('id')
            site = Site.objects.get(repo_name_id=repo_id)
            if site:
                site.git_hash = git_hash
                return site
        return None
