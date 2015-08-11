# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('django_emarsys', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewEventInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_name', models.CharField(max_length=1024)),
                ('recipient_email', models.CharField(max_length=1024)),
                ('context', jsonfield.fields.JSONField(null=True)),
                ('data', jsonfield.fields.JSONField()),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('source', models.CharField(max_length=1024, choices=[('automatic', 'automatic'), ('manual', 'manual')])),
                ('result', models.CharField(max_length=1024, blank=True)),
                ('result_code', models.CharField(max_length=1024, blank=True)),
                ('state', models.CharField(default='sending', max_length=1024, choices=[('sending', 'sending'), ('error', 'error'), ('success', 'success')])),
                ('emarsys_id', models.IntegerField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=1024)),
                ('emarsys_id', models.IntegerField()),
            ],
            options={
                'ordering': ['name'],
                'permissions': [('can_trigger_event', 'Can trigger emarsys events.')],
            },
            bases=(models.Model,),
        ),
    ]
