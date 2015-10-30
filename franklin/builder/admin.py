from django.contrib import admin

from .models import BranchBuild, Environment, Owner, Site, TagBuild


admin.site.register(BranchBuild)
admin.site.register(Environment)
admin.site.register(Owner)
admin.site.register(Site)
admin.site.register(TagBuild)
