# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0005_site_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='url',
            field=models.CharField(max_length=100, default='', db_index=True),
        ),
    ]
