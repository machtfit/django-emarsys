# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf import settings
from django.db import migrations


def migrate_eventinstances(apps, schema_editor):
    EventInstance = apps.get_model('django_emarsys', 'EventInstance')
    NewEventInstance = apps.get_model('django_emarsys', 'NewEventInstance')

    NewEventInstance.objects.all().delete()

    for old_obj in EventInstance.objects.all():
        new_obj = NewEventInstance()
        new_obj.event_name = old_obj.event.name
        new_obj.emarsys_id = old_obj.event.emarsys_id
        new_obj.recipient_email = old_obj.recipient_email
        new_obj.context = json.loads(old_obj.context)
        new_obj.result = old_obj.result
        new_obj.result_code = old_obj.result_code
        new_obj.state = old_obj.state
        new_obj.source = old_obj.source

        data = {}
        for param in old_obj.eventinstancedata_set.all():
            argument = param.event_data.kwarg_name
            name = param.event_data.name
            value = param.object_id
            ct = param.content_type
            model = ct.app_label + '.' + ct.model.capitalize()
            data[argument] = (name, model, value)

        if old_obj.user:
            data['user'] = ('User', 'user.User', old_obj.user_id)

        new_obj.data = data
        new_obj.save()
        # when is an auto_now_add field, so we need to explicitly set again
        new_obj.when = old_obj.when
        new_obj.save()


def migrate_eventinstances_back(apps, schema_editor):
    """
    To reverse this migration Event and EventData have to be filled.
    That information is lost during the migration, so in order to successfully
    revert the EventInstance migration, Event and EventData have to be filled
    beforehand, for instance via fixtures.

    """
    Event = apps.get_model('django_emarsys', 'Event')
    EventData = apps.get_model('django_emarsys', 'EventData')
    EventInstance = apps.get_model('django_emarsys', 'EventInstance')
    EventInstanceData = apps.get_model('django_emarsys', 'EventInstanceData')
    NewEventInstance = apps.get_model('django_emarsys', 'NewEventInstance')
    ContentType = apps.get_model("contenttypes", "ContentType")
    User = apps.get_model(settings.AUTH_USER_MODEL)

    EventInstanceData.objects.all().delete()
    EventInstance.objects.all().delete()

    for new_obj in NewEventInstance.objects.all():
        old_obj = EventInstance()
        old_obj.event = Event.objects.get(name=new_obj.event_name)
        old_obj.recipient_email = new_obj.recipient_email
        old_obj.context = json.dumps(new_obj.context)
        old_obj.result = new_obj.result
        old_obj.result_code = new_obj.result_code
        old_obj.state = new_obj.state
        old_obj.source = new_obj.source
        old_obj.save()
        # when is an auto_now_add field, so we need to explicitly set again
        old_obj.when = new_obj.when
        old_obj.save()

        for argument, (name, model, value) in new_obj.data.items():
            if argument == 'user':
                old_obj.user = User.objects.get(pk=value)
                old_obj.save()
                continue

            old_dataobj = EventInstanceData(event_trigger=old_obj)
            old_dataobj.event_data = EventData.objects.get(
                event=old_obj.event, kwarg_name=argument)
            app_label, model_name = model.rsplit('.', 1)
            old_dataobj.content_type = \
                ContentType.objects.get(
                    app_label=app_label, model=model_name.lower())
            old_dataobj.object_id = value

            old_dataobj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('django_emarsys', '0002_create_newevent_and_neweventinstance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(migrate_eventinstances,
                             migrate_eventinstances_back),
    ]
