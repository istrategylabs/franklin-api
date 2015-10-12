from django.contrib import admin
from .models import Site

class SiteAdmin(admin.ModelAdmin):
    fields = ('owner', 'owner_id', 'repo_name', 'repo_name_id', 'git_hash', \
              'url', 'path', 'oauth_token', 'status')

admin.site.register(Site, SiteAdmin)
