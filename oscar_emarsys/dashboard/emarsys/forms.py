# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.core.urlresolvers import reverse

from oscar.forms.widgets import RemoteSelect
from django_emarsys.event import get_all_parameters_for_event


class EventTriggerForm(forms.Form):
    recipient_email = forms.CharField()

    def __init__(self, event, *args, **kwargs):
        super(EventTriggerForm, self).__init__(*args, **kwargs)
        self.event = event

        for param in get_all_parameters_for_event(self.event.name).values():
            widget = RemoteSelect(
                lookup_url=reverse('dashboard:emarsys-event-data-lookup',
                                   kwargs=dict(pk=event.pk,
                                               argument=param.argument)))
            self.fields[param.argument] = forms.ModelChoiceField(
                label=param.name,
                queryset=param.model_class().objects.all(),
                widget=widget)
