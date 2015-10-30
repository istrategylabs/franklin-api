# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0011_auto_20151029_2054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='build',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='build',
            name='path',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
