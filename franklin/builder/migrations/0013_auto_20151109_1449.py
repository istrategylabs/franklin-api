# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0012_auto_20151104_1902'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='branchbuild',
            options={'verbose_name': 'Branch Build', 'verbose_name_plural': 'Branch Builds'},
        ),
        migrations.AlterModelOptions(
            name='tagbuild',
            options={'verbose_name': 'Tag Build', 'verbose_name_plural': 'Tag Builds'},
        ),
    ]
