# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0007_auto_20151012_1951'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Site',
        ),
    ]
