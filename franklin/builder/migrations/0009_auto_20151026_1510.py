# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0008_auto_20151019_1833'),
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('git_hash', models.CharField(blank=True, null=True, max_length=40)),
                ('branch', models.CharField(blank=True, null=True, max_length=100)),
                ('tag', models.CharField(blank=True, null=True, max_length=100)),
                ('created', models.DateTimeField(editable=False)),
                ('path', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Build',
                'verbose_name_plural': 'Builds',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', max_length=100)),
                ('description', models.TextField(blank=True, default='', max_length=20480)),
                ('deploy_type', models.CharField(default='BCH', max_length=3, choices=[('BCH', 'Any push to a branch'), ('TAG', 'Any commit matching a tag regex'), ('PRO', 'Manually from a lower environment')])),
                ('branch', models.CharField(default='master', max_length=100)),
                ('tag_regex', models.CharField(blank=True, max_length=100)),
                ('url', models.CharField(blank=True, default='', max_length=100, db_index=True)),
                ('status', models.CharField(default='REG', max_length=3, choices=[('REG', 'Webhook Registered'), ('BLD', 'Building Now'), ('SUC', 'Deploy Succeeded'), ('FAL', 'Deploy Failed')])),
                ('current_deploy', models.ForeignKey(blank=True, related_name='deployments', to='builder.Build', null=True)),
                ('past_builds', models.ManyToManyField(blank=True, related_name='environments', to='builder.Build')),
            ],
            options={
                'verbose_name': 'Environment',
                'verbose_name_plural': 'Environments',
            },
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('github_id', models.PositiveIntegerField(unique=True)),
                ('deploy_key', models.CharField(default='', max_length=255)),
                ('owner', models.ForeignKey(related_name='sites', to='builder.Owner')),
            ],
            options={
                'verbose_name': 'Site',
                'verbose_name_plural': 'Sites',
            },
        ),
        migrations.AddField(
            model_name='environment',
            name='site',
            field=models.ForeignKey(related_name='environments', to='builder.Site'),
        ),
        migrations.AddField(
            model_name='build',
            name='site',
            field=models.ForeignKey(related_name='builds', to='builder.Site'),
        ),
        migrations.AlterUniqueTogether(
            name='environment',
            unique_together=set([('name', 'site')]),
        ),
    ]
