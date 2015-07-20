# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0002_site_repo_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='path',
            field=models.CharField(max_length=100),
        ),
    ]
