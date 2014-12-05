# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models

from . import api


class EventManager(models.Manager):
    def sync_events(self):
        """
        Sync locally available events, identified by their name, with emarsys.

        In particular:
            * Add events that don't exist locally.
            * Add missing emarsys event ids.
            * Disable events that don't exist on emarsys by setting their
              emarsys_id to None. Events are not deleted so as to not lose
              associated EventData information.

        Events are identified by their name. This allows adding and
        implementing events in advance without knowing their emarsys id.
        Syncing will then add the emarsys id to the events so that they can be
        triggered.
        """
        emarsys_events = api.get_events()
        for local_event in self.all():
            emarsys_event_id = emarsys_events.get(local_event.name)
            if emarsys_event_id:
                local_event.emarsys_id = emarsys_event_id
                del emarsys_events[local_event.name]
            else:
                local_event.emarsys_id = None
            local_event.save()

        for emarsys_event_name, emarsys_event_id in emarsys_events.items():
            self.create(emarsys_id=emarsys_event_id, name=emarsys_event_name)

    def trigger(self, event_name, email, async=False, **kwargs):
        event = self.get(name=event_name, emarsys_id__isnull=False)
        event.trigger(email, async, **kwargs)
