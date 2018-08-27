# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('emarsys_id', models.IntegerField(unique=True, null=True)),
                ('name', models.CharField(unique=True, max_length=1024, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'permissions': [('can_trigger_event', 'Can trigger emarsys events.')],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('kwarg_name', models.CharField(max_length=1024)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE), ),
                ('event', models.ForeignKey(to='django_emarsys.Event', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('recipient_email', models.CharField(max_length=1024)),
                ('context', models.TextField()),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('source', models.CharField(max_length=1024, choices=[('automatic', 'automatic'), ('manual', 'manual')])),
                ('result', models.CharField(max_length=1024, blank=True)),
                ('result_code', models.CharField(max_length=1024, blank=True)),
                ('state', models.CharField(default='sending', max_length=1024, choices=[('sending', 'sending'), ('error', 'error'), ('success', 'success')])),
                ('event', models.ForeignKey(to='django_emarsys.Event', on_delete=django.db.models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventInstanceData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE)),
                ('event_data', models.ForeignKey(to='django_emarsys.EventData', on_delete=django.db.models.deletion.CASCADE)),
                ('event_trigger', models.ForeignKey(to='django_emarsys.EventInstance', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='eventinstancedata',
            unique_together=set([('event_trigger', 'event_data')]),
        ),
        migrations.AlterUniqueTogether(
            name='eventdata',
            unique_together=set([('event', 'kwarg_name'), ('event', 'name')]),
        ),
        migrations.AddField(
            model_name='event',
            name='kwargs',
            field=models.ManyToManyField(to='contenttypes.ContentType', through='django_emarsys.EventData'),
            preserve_default=True,
        ),
    ]
