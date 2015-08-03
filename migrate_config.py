#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

event_fixture = json.load(open('event.json'))
eventdata_fixture = json.load(open('eventdata.json'))
eventinstance_fixture = json.load(open('eventinstance.json'))

events_with_user = set()
for obj in eventinstance_fixture:
    if obj['fields']['user']:
        events_with_user.add(obj['fields']['event'])

events = {}

for obj in event_fixture:
    events[obj['pk']] = obj
    obj['params'] = {}

for obj in eventdata_fixture:
    if obj['model'] == 'django_emarsys.eventdata':
        event_obj = events[obj['fields']['event']]
        event_obj['params'][obj['fields']['kwarg_name']] = obj['fields']

event_config = {}

for unused_event_id, event_obj in events.items():
    event_config[event_obj['fields']['name']] = {
        arg: (params['name'], '.'.join(params['content_type'][:-1]) +
              '.' + params['content_type'][-1].capitalize())
        for arg, params in event_obj['params'].items()
    }
    if event_obj['pk'] in events_with_user:
        event_config[event_obj['fields']['name']]['user'] = \
            ('User', 'auth.User')

print "EMARSYS_EVENTS = {"
for event_name, params in sorted(event_config.items(),
                                 lambda a, b: cmp(a[0], b[0])):
    print u'    "{}": {{'.format(event_name.replace('"', '\"'))
    for argument, (name, model) in sorted(params.items(),
                                          lambda a, b: cmp(a[0], b[0])):
        print u'        "{}": ("{}", "{}"),'\
            .format(argument.replace('"', '\"'),
                    name.replace('"', '\"'),
                    model.replace('"', '\"'))
    print '    },'
print "}"
