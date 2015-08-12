# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from django.conf import settings
from django.utils.html import conditional_escape

from emarsys import EmarsysError

from . import api
from .context_provider_registry import get_context_provider
from .exceptions import (BadDataError, DjangoEmarsysError,
                         UnknownEventNameError)
from .models import Event, EventInstance, EventParam

log = logging.getLogger(__name__)


def get_all_parameters_for_event(event_name):
        return {argument: get_parameter_for_event(event_name, argument)
                for argument in settings.EMARSYS_EVENTS[event_name].keys()}


def get_parameter_for_event(event_name, argument):
    name, model = settings.EMARSYS_EVENTS[event_name][argument]
    return EventParam(
        argument=argument,
        name=name,
        model=model
    )


def get_event_id(name):
    try:
        return Event.objects.get(name=name).emarsys_id
    except Event.DoesNotExist:
        pass

    log.info("Emarsys-ID for event '{name}' unknown, "
             "syncing...".format(name=name))

    sync_events()

    try:
        return Event.objects.get(name=name).emarsys_id
    except Event.DoesNotExist:
        pass

    return None


def sync_events():
    """
    Sync locally available events, identified by their name, with emarsys.

    In particular:
        * Add events that don't exist locally.
        * Update changed IDs.
        * Delete Event objects if their name isn't reported by Emarsys
          anymore. There are no foreign keys pointing to Event, so this
          is safe.

    Events are identified by their name. This allows adding and
    implementing events in advance without knowing their emarsys id.
    Syncing will then add a Event object with the emarsys ID so that they
    can be triggered.

    :return: num_new_events
    """
    num_new_events = 0
    num_updated_ids = 0
    num_deleted_ids = 0
    unsynced_event_names = []

    try:
        emarsys_events = api.get_events()
    except EmarsysError as e:
        log.error('Emarsys error: {}\n'.format(e))
        return num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names

    known_event_names = set(settings.EMARSYS_EVENTS.keys())

    for local_event in Event.objects.all():
        emarsys_event_id = emarsys_events.get(local_event.name)
        if not emarsys_event_id or local_event.name not in known_event_names:
            local_event.delete()
            num_deleted_ids += 1
        else:
            if local_event.emarsys_id != emarsys_event_id:
                num_updated_ids += 1

            local_event.emarsys_id = emarsys_event_id
            del emarsys_events[local_event.name]
            local_event.save()

    for emarsys_event_name, emarsys_event_id in emarsys_events.items():
        if emarsys_event_name not in known_event_names:
            continue

        Event.objects.create(emarsys_id=emarsys_event_id,
                             name=emarsys_event_name)
        num_new_events += 1

    all_synced_event_names = set(Event.objects.all()
                                 .values_list('name', flat=True))
    unsynced_event_names = list(known_event_names - all_synced_event_names)

    if unsynced_event_names:
        log.warning("these event names in settings.EMARSYS_EVENTS are not "
                    "known by Emarsys: {}"
                    .format(', '.join(
                        '"{}"'.format(x.replace('"', '\\"'))
                            for x in unsynced_event_names)))

    return num_new_events, num_updated_ids, num_deleted_ids, \
        unsynced_event_names


def get_placeholder_data(event_name, **kwargs):
    context_provider = get_context_provider(event_name)

    return context_provider(**kwargs)


def trigger_event(event_name, recipient_email, data=None,
                  create_user_if_needed=True,
                  contact_data_provider=None,
                  manual=False):
    if manual:
        source = EventInstance.SOURCE_MANUAL
    else:
        source = EventInstance.SOURCE_AUTOMATIC

    emarsys_event_id = get_event_id(event_name)

    event = _create_event_instance(
        event_name=event_name,
        recipient_email=recipient_email,
        emarsys_event_id=emarsys_event_id,
        source=source,
        data=data)

    if (event.state == EventInstance.STATE_ERROR
            and event.result_code == '2008'
            and create_user_if_needed):

        if contact_data_provider is not None:
            contact_data = contact_data_provider()
        else:
            contact_data = {'E-Mail': recipient_email}

        api.create_contact(contact_data)
        event = _create_event_instance(
            event_name=event_name,
            recipient_email=recipient_email,
            emarsys_event_id=emarsys_event_id,
            source=source,
            data=data)

    return event


def _create_event_instance(event_name, recipient_email, emarsys_event_id,
                           source, data):
    """
    A `EventInstance` object is instantiated. All data validation is
    done here, passing along correct user `data`.

    Upon any error the resulting event instance's will store the error message
    and get the appropriate state.

    :returns: the new event object

    """
    event = EventInstance.objects.create(
        event_name=event_name,
        recipient_email=recipient_email,
        source=source,
        emarsys_id=emarsys_event_id)

    if data is None:
        data = {}

    try:
        context = {'global': {
            key: conditional_escape(value)
            for key, value
            in get_placeholder_data(event.event_name, **data).items()}}

        event.set_context(context)

        if event_name not in settings.EMARSYS_EVENTS:
            raise UnknownEventNameError(event_name)

        event_params = get_all_parameters_for_event(event_name)

        expected_params = set(event_params.keys())
        given_params = set(data.keys())

        if given_params != expected_params:
            raise BadDataError(expected_params, given_params)

        for param in event_params.values():
            if not isinstance(data[param.argument], param.model_class()):
                raise ValueError("expected instance of '{model}' for "
                                 "argument '{argument}': '{value}'"
                                 .format(model=param.model,
                                         argument=param.argument,
                                         value=data[param.argument]))

            event.set_parameter(param, data[param.argument])

    except (DjangoEmarsysError, ValueError) as e:
        event.handle_error(e)
        return event

    if not emarsys_event_id:
        event.handle_error("Emarsys-ID unknown")
        return event

    if getattr(settings, 'EMARSYS_RECIPIENT_WHITELIST', None) is not None:
        if recipient_email not in settings.EMARSYS_RECIPIENT_WHITELIST:
            event.handle_error("User not on whitelist: {}"
                               .format(recipient_email))
            return event

    try:
        api.trigger_event(emarsys_event_id, recipient_email, context)
    except EmarsysError as e:
        event.handle_emarsys_error(e)
        return event

    event.handle_success()
    return event
