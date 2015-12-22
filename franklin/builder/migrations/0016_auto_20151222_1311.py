# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0015_auto_20151209_1701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='url',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
