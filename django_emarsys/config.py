# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from collections import Counter
from itertools import chain

from django.apps import apps
from django.conf import settings
from django.core.checks import Critical, Error, Warning

from .models import EventParam


_VALID_ARG = re.compile(r'^[a-z][a-z0-9_]*$')


def _flatten(l):
    """
    Flatten a list of lists into a list
    """
    return list(chain.from_iterable(l))


def _find_duplicates(l):
    """
    Return non-unique elements in a list.

    Should be in Python.
    """
    return [item for item, count in Counter(l).items() if count > 1]


def validate_settings():
    """
    Turn settings into a configuration dict that `validate_configuration` can
    check.

    """
    # The extra `hasattr()` check is necessary to make this work with
    # overridden settings from tests. If a setting existed in the original
    # settings object, but is then deleted in overridden settings, then
    # `dir()` will report it present, but accessing it raises an
    # `AttributeError`.
    #
    # Minimal test for this:
    #
    # >>> from django.conf import settings
    # >>> from django.test.utils import override_settings
    # >>> @override_settings()
    # >>> def test_strange_dir_issue():
    # >>>     delattr(settings, 'DEBUG')
    # >>>     assert 'DEBUG' in dir(settings)
    # >>>     assert not hasattr(settings, 'DEBUG')
    # >>>
    # >>> test_strange_dir_issue()
    return validate_configuration({key: getattr(settings, key)
                                  for key in dir(settings)
                                  if hasattr(settings, key)})


def validate_configuration(config):
    """
    Validate EMARSYS_* configurations based on a dict representing settings.

    The expected structure for `EMARSYS_EVENTS` is this:

    >>> EMARSYS_EVENTS = {
        '<event name>': {
            '<argument name>': ('<name>', '<app>.<model>'),
            '<argument name>': ('<name>', '<app>.<model>'),
            [...]
        },
        '<event name>': {
            '<argument name>': ('<name>', '<app>.<model>'),
            '<argument name>': ('<name>', '<app>.<model>'),
            [...]
        },
        [...]
    }

    """
    messages = []
    if not config.get('EMARSYS_ACCOUNT'):
        messages.append(Critical("EMARSYS_ACCOUNT not set"))

    if not config.get('EMARSYS_PASSWORD'):
        messages.append(Critical("EMARSYS_PASSWORD not set"))

    if not config.get('EMARSYS_BASE_URI'):
        messages.append(Critical("EMARSYS_BASE_URI not set"))

    events = config.get('EMARSYS_EVENTS')
    if events is None:
        messages.append(Critical("EMARSYS_EVENTS not set"))
        return messages

    if not isinstance(events, dict):
        messages.append(Critical("EMARSYS_EVENTS must be a dict"))
        return messages

    if not events:
        messages.append(Warning("EMARSYS_EVENTS is empty"))
        return messages

    messages += _flatten(_validate_event(event, params)
                         for event, params
                         in events.items())

    return messages


def _validate_event(event, params):
    """
    Validate a single event, where `event` is a string and `params` is a `dict`
    of `tuple`s of the form:

    >>> params = {
        '<argument name>': ('<name>', '<app>.<model>'),
        '<argument name>': ('<name>', '<app>.<model>'),
        [...]
    }

    """
    if not isinstance(event, basestring) or not event:
        return [Warning("invalid event name: '{event}'".format(event=event))]

    messages = []

    # params[0] is expected to be the name
    duplicate_names = _find_duplicates([param[0]
                                        for param in params.values()
                                        if len(param) > 0])
    if duplicate_names:
        messages.append(
            Warning("reused parameter name for event '{event}': '{keys}'"
                    .format(keys=", ".join(duplicate_names), event=event)))

    return messages + _flatten(
        _validate_event_param(event, argument, param)
        for argument, param in params.items())


def _validate_event_param(event, argument, param):
    """
    Validate the argument name and the event parameters for it.

    The expected structure of `param`:

    >>> param = ('<name>', '<app>.<model>')

    """
    messages = []

    if not _VALID_ARG.match(argument):
        messages.append(
            Error("invalid parameter argument for event '{event}': "
                  "'{argument}'"
                  .format(argument=argument, event=event)))

    if not isinstance(param, (tuple, list)) or len(param) != 2:
        messages.append(
            Error("invalid parameter definition '{event}': "
                  "'{argument}' => {param}"
                  .format(param=param, argument=argument, event=event)))

        return messages

    name, type_ = param
    event_param = EventParam(argument, name, type_)

    if not isinstance(name, basestring) or not name:
        messages.append(
            Error("invalid parameter name for event '{event}': '{name}'"
                  .format(name=name, event=event)))

    try:
        apps.get_model(event_param.model)
    except (AttributeError, LookupError, ValueError) as e:
        # AttributeError occurs when "model" is not a string, because
        # get_model calls model.rsplit()
        # ValueError occurs when "model" doesn't contain a period and
        # therefore .rsplit() results in only one value to unpack
        # LookupError occurs when either the app or model name in
        # "model" don't exist
        messages.append(
            Error("bad model '{model}' for event '{event}': {error}"
                  .format(model=event_param.model, event=event, error=e)))

    return messages
