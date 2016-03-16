# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0017_auto_20160216_1953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='deploy_type',
            field=models.CharField(choices=[('BCH', 'branch'), ('TAG', 'tag'), ('PRO', 'promote')], default='BCH', max_length=3),
        ),
        migrations.AlterField(
            model_name='environment',
            name='status',
            field=models.CharField(choices=[('REG', 'registered'), ('BLD', 'building'), ('SUC', 'success'), ('FAL', 'failed')], default='REG', max_length=3),
        ),
    ]
