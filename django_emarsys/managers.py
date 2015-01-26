# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys

from django.db import models

from emarsys import EmarsysError

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
        num_new_events = 0
        num_added_ids = 0
        num_updated_ids = 0
        num_deleted_ids = 0

        try:
            emarsys_events = api.get_events()
            for local_event in self.all():
                emarsys_event_id = emarsys_events.get(local_event.name)
                if emarsys_event_id:
                    if not local_event.emarsys_id:
                        num_added_ids += 1
                    elif local_event.emarsys_id != emarsys_event_id:
                        num_updated_ids += 1

                    local_event.emarsys_id = emarsys_event_id
                    del emarsys_events[local_event.name]
                else:
                    if local_event.emarsys_id:
                        num_deleted_ids += 1
                    local_event.emarsys_id = None

                local_event.save()

            for emarsys_event_name, emarsys_event_id in emarsys_events.items():
                self.create(emarsys_id=emarsys_event_id, name=emarsys_event_name)
                num_new_events += 1
        except EmarsysError as e:
            sys.stderr.write('Emarsys error: {}\n'.format(e))

        return num_new_events, num_added_ids, num_updated_ids, num_deleted_ids

    def trigger(self, event_name, recipient_email, user=None, data=None,
                create_user_if_needed=True, async=False):
        event = self.get(name=event_name)
        event_instance = event.trigger(
            recipient_email, user, data, async=async)

        if event_instance.state == 'error':
            if event_instance.result_code == '2008':
                if create_user_if_needed:
                    api.create_contact(recipient_email)
                    event_instance = event.trigger(
                        recipient_email, user, data, async=async)

        return event_instance
