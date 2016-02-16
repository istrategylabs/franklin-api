# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0016_auto_20151222_1311'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='deploy_key_id',
            field=models.CharField(null=True, max_length=12, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='site',
            name='webhook_id',
            field=models.CharField(null=True, max_length=12, blank=True),
        ),
    ]
