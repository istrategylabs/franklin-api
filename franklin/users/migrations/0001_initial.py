# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('sites', models.ManyToManyField(related_name='admins', to='builder.Site')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='details')),
            ],
            options={
                'verbose_name': 'Detail',
                'verbose_name_plural': 'Details',
            },
        ),
    ]
