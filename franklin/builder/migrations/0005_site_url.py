# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0004_auto_20150819_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='url',
            field=models.CharField(default='', max_length=100),
        ),
    ]
