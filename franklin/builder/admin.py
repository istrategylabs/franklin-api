from django.contrib import admin
from .models import Site

class SiteAdmin(admin.ModelAdmin):
    fields = ('repo_name', 'git_hash', 'url', 'path')

admin.site.register(Site, SiteAdmin)
