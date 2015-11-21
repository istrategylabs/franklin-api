# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0014_auto_20151112_2211'),
        ('users', '0002_auto_20151030_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetails',
            name='sites',
            field=models.ManyToManyField(to='builder.Site', related_name='admins'),
        ),
    ]
