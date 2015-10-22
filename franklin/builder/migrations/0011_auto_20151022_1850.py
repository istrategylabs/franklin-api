# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0010_auto_20151020_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='build',
            name='branch',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='build',
            name='tag',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='build',
            name='git_hash',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
