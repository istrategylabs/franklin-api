# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0003_auto_20150720_1143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='git_hash',
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name='site',
            name='repo_name',
            field=models.CharField(max_length=100),
        ),
    ]
