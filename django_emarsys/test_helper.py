# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
from collections import namedtuple

from .models import NewEventInstance

Event = namedtuple('Event', 'name context')


class EmarsysTestMixin(object):
    def assertEmarsysEvents(self, events, all=True):
        """
        Check that the given events have been triggered. If `all` is `True`,
        check that no other events have been triggered.

        `events` is a list of strings, representing the events to be
        checked.

        The matched event objects are returned in the order that they appeared
        in `events`.
        """
        ret_events = []

        for i, event_name in enumerate(events):
            instance = \
                NewEventInstance.objects.filter(event_name=event_name).first()

            self.assertIsNotNone(
                instance, "Event no. {} '{}' not found.".format(i, event_name))

            ret_events.append(
                Event(name=instance.event_name,
                      context=instance.context['global']))

            instance.delete()

        if all:
            self.assertEqual(
                0, NewEventInstance.objects.count(),
                "More events have been triggered:\n{}"
                .format(", ".join(instance.event_name
                                  for instance in
                                  NewEventInstance.objects.all())))

        return ret_events

    def resetEmarsysEvents(self):
        NewEventInstance.objects.all().delete()
