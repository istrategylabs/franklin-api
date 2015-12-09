# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0014_auto_20151112_2211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='url',
            field=models.CharField(default='', blank=True, max_length=100, unique=True),
        ),
    ]
