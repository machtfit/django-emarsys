"""
A context provider transforms python data (``kwargs``) into emarsys event data.
"""

import functools

from django.conf import settings

context_providers = {}


class ContextProviderException(Exception):
    pass


def register_context_provider(event_name):
    def _dec(func):
        if event_name in context_providers:
            if event_name:
                provider_name = ("context provider for event {}"
                                 .format(event_name))
            else:
                provider_name = "general context provider"
            raise Exception(
                "Attempted to register second {}".format(provider_name))

        provider_function = functools.partial(func, event_name=event_name)
        context_providers[event_name] = provider_function

        return func
    return _dec


def get_context_provider(event_name):
    try:
        return context_providers[event_name]
    except KeyError:
        try:
            return context_providers[None]
        except KeyError:
            raise ContextProviderException(
                "No context provider registered for event '{}' and"
                " no general context provider registered either."
                .format(event_name))


if settings.EMARSYS_USE_NULL_GENERIC_CONTEXT_PROVIDER:
    @register_context_provider(None)
    def null_context_provider(event_name, **kwargs):
        return {}
