# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_emarsys', '0003_migrate_eventinstances'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='kwargs',
        ),
        migrations.AlterUniqueTogether(
            name='eventdata',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='eventdata',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='eventdata',
            name='event',
        ),
        migrations.RemoveField(
            model_name='eventinstance',
            name='event',
        ),
        migrations.DeleteModel(
            name='Event',
        ),
        migrations.RemoveField(
            model_name='eventinstance',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='eventinstancedata',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='eventinstancedata',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='eventinstancedata',
            name='event_data',
        ),
        migrations.DeleteModel(
            name='EventData',
        ),
        migrations.RemoveField(
            model_name='eventinstancedata',
            name='event_trigger',
        ),
        migrations.DeleteModel(
            name='EventInstance',
        ),
        migrations.DeleteModel(
            name='EventInstanceData',
        ),
        migrations.RenameModel(
            old_name='NewEvent',
            new_name='Event',
        ),
        migrations.RenameModel(
            old_name='NewEventInstance',
            new_name='EventInstance',
        ),
    ]
