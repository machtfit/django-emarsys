# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple
import json

from django_emarsys.models import EventInstance

Event = namedtuple('Event', 'name context')


class EmarsysTestMixin(object):
    def assertEmarsysEvents(self, events, all=True):
        """
        Check that the given events have been triggered. If `all` is `True`,
        check that no other events have been triggered.

        `events` is a list of tuples or strings, representing the events to be
        checked.

        2-tuple events contain the event name and user.

        string events are just the event name; the user is not checked.

        The matched event objects are returned in the order that they appeared
        in `events`.
        """
        ret_events = []

        for i, event in enumerate(events):
            user = None
            if isinstance(event, tuple):
                event_name, user = event
            else:
                event_name = event

            instances = EventInstance.objects.filter(event__name=event_name)

            if user:
                instances = instances.filter(user_id=user.pk)

            instance = instances.first()

            self.assertIsNotNone(
                instance, "Event no. {} '{}' not found.".format(i, event_name))

            ret_events.append(
                Event(name=instance.event.name,
                      context=json.loads(instance.context)['global']))

            instance.delete()

        if all:
            self.assertEqual(
                0, EventInstance.objects.count(),
                "More events have been triggered:\n{}"
                .format(", ".join(instance.event.name
                                  for instance in
                                  EventInstance.objects.all())))

        return ret_events

    def resetEmarsysEvents(self):
        EventInstance.objects.all().delete()
