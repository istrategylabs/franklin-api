# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('path', models.CharField(max_length=100, blank=True)),
                ('status', models.CharField(max_length=3, choices=[('NEW', 'new'), ('BLD', 'building'), ('SUC', 'success'), ('FAL', 'failed')], default='NEW')),
            ],
        ),
        migrations.CreateModel(
            name='Deploy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('deployed', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100, default='')),
                ('deploy_type', models.CharField(max_length=3, choices=[('BCH', 'branch'), ('TAG', 'tag'), ('PRO', 'promote')], default='BCH')),
                ('branch', models.CharField(max_length=100, default='master')),
                ('tag_regex', models.CharField(max_length=100, blank=True)),
                ('url', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Environment',
                'verbose_name_plural': 'Environments',
            },
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
                ('github_id', models.PositiveIntegerField(unique=True)),
            ],
            options={
                'verbose_name': 'Owner',
                'verbose_name_plural': 'Owners',
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
                ('github_id', models.PositiveIntegerField(unique=True)),
                ('deploy_key', models.TextField(blank=True, null=True)),
                ('deploy_key_secret', models.TextField(blank=True, null=True)),
                ('deploy_key_id', models.CharField(max_length=12, null=True, blank=True)),
                ('webhook_id', models.CharField(max_length=12, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(to='builder.Owner', related_name='sites')),
            ],
            options={
                'verbose_name': 'Site',
                'verbose_name_plural': 'Sites',
            },
        ),
        migrations.CreateModel(
            name='BranchBuild',
            fields=[
                ('build_ptr', models.OneToOneField(parent_link=True, to='builder.Build', serialize=False, primary_key=True, auto_created=True)),
                ('git_hash', models.CharField(max_length=40)),
                ('branch', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Branch Build',
                'verbose_name_plural': 'Branch Builds',
            },
            bases=('builder.build',),
        ),
        migrations.CreateModel(
            name='TagBuild',
            fields=[
                ('build_ptr', models.OneToOneField(parent_link=True, to='builder.Build', serialize=False, primary_key=True, auto_created=True)),
                ('tag', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Tag Build',
                'verbose_name_plural': 'Tag Builds',
            },
            bases=('builder.build',),
        ),
        migrations.AddField(
            model_name='environment',
            name='past_builds',
            field=models.ManyToManyField(blank=True, related_name='environments', to='builder.Build', through='builder.Deploy'),
        ),
        migrations.AddField(
            model_name='environment',
            name='site',
            field=models.ForeignKey(to='builder.Site', related_name='environments'),
        ),
        migrations.AddField(
            model_name='deploy',
            name='build',
            field=models.ForeignKey(to='builder.Build'),
        ),
        migrations.AddField(
            model_name='deploy',
            name='environment',
            field=models.ForeignKey(to='builder.Environment'),
        ),
        migrations.AddField(
            model_name='build',
            name='site',
            field=models.ForeignKey(to='builder.Site', related_name='builds'),
        ),
        migrations.AlterUniqueTogether(
            name='environment',
            unique_together=set([('name', 'site')]),
        ),
        migrations.AlterUniqueTogether(
            name='branchbuild',
            unique_together=set([('git_hash', 'branch')]),
        ),
    ]
