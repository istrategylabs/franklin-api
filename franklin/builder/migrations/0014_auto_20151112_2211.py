# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0013_auto_20151110_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='deploy_key_secret',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='deploy_key',
            field=models.TextField(blank=True, null=True),
        ),
    ]
