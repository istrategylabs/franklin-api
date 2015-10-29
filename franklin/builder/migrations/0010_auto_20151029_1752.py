# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0009_auto_20151026_1510'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='build',
            options={},
        ),
        migrations.RemoveField(
            model_name='build',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='build',
            name='git_hash',
        ),
        migrations.RemoveField(
            model_name='build',
            name='tag',
        ),
    ]
