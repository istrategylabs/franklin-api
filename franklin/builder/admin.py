from django.contrib import admin

from .models import BranchBuild, Deploy, Environment, Owner, Site


class EnvironmentBuildInline(admin.TabularInline):
    model = Deploy
    extra = 1


class BranchBuildAdmin(admin.ModelAdmin):
    inlines = (EnvironmentBuildInline, )


class EnvironmentAdmin(admin.ModelAdmin):
    inlines = (EnvironmentBuildInline, )

admin.site.register(BranchBuild, BranchBuildAdmin)
admin.site.register(Deploy)
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Owner)
admin.site.register(Site)
