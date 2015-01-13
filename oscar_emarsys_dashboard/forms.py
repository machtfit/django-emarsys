# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.core.urlresolvers import reverse

from oscar.core.compat import get_user_model
from oscar.forms.widgets import RemoteSelect


class EventTriggerForm(forms.Form):
    recipient_email = forms.CharField(required=False)
    user = forms.ModelChoiceField(queryset=None)

    def __init__(self, event, *args, **kwargs):
        super(EventTriggerForm, self).__init__(*args, **kwargs)
        self.event = event

        self.fields['user'].queryset = get_user_model().objects.all()
        self.fields['user'].widget = RemoteSelect(
            lookup_url=reverse('dashboard:emarsys-event-data-lookup',
                               kwargs=dict(pk=event.pk, name='user')))

        for event_data in event.eventdata_set.all():
            widget = RemoteSelect(
                lookup_url=reverse('dashboard:emarsys-event-data-lookup',
                                   kwargs=dict(pk=event.pk,
                                               name=event_data.kwarg_name)))
            self.fields[event_data.kwarg_name] = forms.ModelChoiceField(
                label=event_data.name,
                queryset=event_data.content_type.model_class().objects.all(),
                widget=widget)
