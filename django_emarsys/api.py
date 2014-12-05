# -*- coding: utf-8 -*-

import emarsys

from django.conf import settings


client = emarsys.Emarsys(settings.EMARSYS_ACCOUNT,
                         settings.EMARSYS_PASSWORD,
                         settings.EMARSYS_BASE_URI)


def get_events():
    response = client.call('/api/v2/event', 'GET')
    return {event['name']: event['id'] for event in response}


def trigger_event(event_id, email, context):
    client.call(
        '/api/v2/event/{}/trigger'.format(event_id), 'POST',
        {
            "key_id": 3,
            "external_id": email,
            "data": context
        }
    )
