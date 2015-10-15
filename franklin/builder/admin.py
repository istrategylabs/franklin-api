from django.contrib import admin
from builder.models import Build, Environment, Owner, Site


admin.site.register(Build)
admin.site.register(Environment)
admin.site.register(Owner)
admin.site.register(Site)
