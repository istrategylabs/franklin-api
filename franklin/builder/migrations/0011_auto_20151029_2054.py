# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0010_auto_20151029_1752'),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchBuild',
            fields=[
                ('build_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='builder.Build', serialize=False, parent_link=True)),
                ('git_hash', models.CharField(max_length=40)),
                ('branch', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'BranchBuild',
                'verbose_name_plural': 'BranchBuilds',
            },
            bases=('builder.build',),
        ),
        migrations.CreateModel(
            name='TagBuild',
            fields=[
                ('build_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='builder.Build', serialize=False, parent_link=True)),
                ('tag', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'TagBuild',
                'verbose_name_plural': 'TagBuilds',
            },
            bases=('builder.build',),
        ),
        migrations.AlterUniqueTogether(
            name='branchbuild',
            unique_together=set([('git_hash', 'branch')]),
        ),
    ]
