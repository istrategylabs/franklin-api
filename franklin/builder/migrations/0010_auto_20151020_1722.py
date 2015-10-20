# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0009_auto_20151020_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='current_deploy',
            field=models.ForeignKey(to='builder.Build', blank=True, related_name='deployments', null=True),
        ),
        migrations.AlterField(
            model_name='environment',
            name='past_builds',
            field=models.ManyToManyField(to='builder.Build', blank=True, related_name='environments'),
        ),
        migrations.AlterField(
            model_name='environment',
            name='tag_regex',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='environment',
            name='url',
            field=models.CharField(db_index=True, default='', max_length=100, blank=True),
        ),
    ]
