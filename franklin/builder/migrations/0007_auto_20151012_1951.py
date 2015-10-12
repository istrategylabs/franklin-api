# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0006_auto_20150901_2134'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='oauth_token',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='site',
            name='owner',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='site',
            name='owner_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='repo_name_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='status',
            field=models.CharField(choices=[('REG', 'Webhook Registered'), ('BLD', 'Building Now'), ('SUC', 'Deploy Succeeded'), ('FAL', 'Deploy Failed')], default='REG', max_length=3),
        ),
    ]
