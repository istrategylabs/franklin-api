# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tagbuild',
            name='build_ptr',
        ),
        migrations.RemoveField(
            model_name='build',
            name='path',
        ),
        migrations.AddField(
            model_name='build',
            name='uuid',
            field=models.UUIDField(editable=False, default=uuid.uuid4),
        ),
        migrations.DeleteModel(
            name='TagBuild',
        ),
    ]
