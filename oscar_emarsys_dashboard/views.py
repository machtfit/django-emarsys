# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from emarsys import EmarsysError

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import Form
from django.utils.http import urlencode
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.edit import FormView

from django_tables2 import SingleTableView

from oscar.core.compat import get_user_model
from oscar.views.generic import ObjectLookupView

from apps.views import SearchMixin, SearchFormMixin

from django_emarsys.models import Event, EventInstance
from django_emarsys.context_provider_registry import ContextProviderException

from .forms import EventTriggerForm
from .tables import EventTable, EventInstanceTable


class EventListView(SearchFormMixin, SearchMixin, SingleTableView):
    model = Event
    table_class = EventTable
    template_name = 'dashboard/emarsys/event_list.html'

    search = {
        'name': 'name__icontains',
        'id': 'emarsys_id',
    }

    search_types = {
        'id': int
    }


class EventsSyncView(FormView):
    form_class = Form

    def form_valid(self, form):
        try:
            Event.objects.sync_events()
            messages.success(self.request, 'Events gesynct.')
        except EmarsysError as e:
            messages.error(self.request, 'Emarsys error: {}'.format(e))
        return super(EventsSyncView, self).form_valid(form)

    def get_success_url(self):
        return "{}?{}".format(reverse('dashboard:emarsys-event-list'),
                              urlencode(self.request.GET, doseq=True))


class EventTriggerMixin(object):
    model = Event
    context_object_name = 'event'
    form_class = EventTriggerForm
    template_name = 'dashboard/emarsys/event_trigger.html'

    def get(self, *args, **kwargs):
        self.event = self.object = self.get_object()
        return super(EventTriggerMixin, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.event = self.object = self.get_object()
        return super(EventTriggerMixin, self).post(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EventTriggerMixin, self).get_form_kwargs()
        kwargs['event'] = self.event
        return kwargs


class EventTriggerView(EventTriggerMixin, SingleObjectMixin, FormView):
    def get_context_data(self, **kwargs):
        context = super(EventTriggerView, self).get_context_data(**kwargs)
        form = kwargs.get('form')
        if form and form.is_bound:
            data = self.event.get_placeholder_data(**form.cleaned_data)
            context['placeholder_data'] = sorted(data.items())
        return context

    def form_valid(self, form):
        if not self.event.emarsys_id:
            Event.objects.sync_events()
            self.event = Event.objects.get(pk=self.event.pk)

        event_instance = self.event.trigger(
            user=form.cleaned_data.pop('user'),
            data=form.cleaned_data,
            source='manual')

        if event_instance.state != 'success':
            messages.error(self.request, event_instance.result)
        else:
            messages.success(self.request,
                             "Event '{}' wurde getriggert.".format(self.event))

        # redisplay form even if it was valid - this allows the user to easily
        # trigger the same event again for testing
        return super(EventTriggerView, self).form_invalid(form)


class EventPlaceholderDataView(EventTriggerMixin, SingleObjectMixin, FormView):
    template_name = 'dashboard/emarsys/partials/placeholder_data.html'

    def get_context_data(self, **kwargs):
        context = super(EventPlaceholderDataView, self).get_context_data(
            **kwargs)
        form = kwargs.get('form')
        if form and form.is_bound:
            try:
                data = self.event.get_placeholder_data(**form.cleaned_data)
            except ContextProviderException as e:
                context['placeholder_data_error'] = e
            else:
                context['placeholder_data'] = sorted(data.items())
        return context

    def form_valid(self, form):
        # Always just display the template
        return self.form_invalid(form)


class EventDataLookupView(EventTriggerMixin, SingleObjectMixin,
                          ObjectLookupView):
    def get(self, *args, **kwargs):
        self.kwarg_name = kwargs.pop('name')
        return super(EventDataLookupView, self).get(*args, **kwargs)

    def get_lookup_queryset(self):
        if self.kwarg_name == 'user':
            self.model = get_user_model()
        else:
            event_data = self.event.eventdata_set.get(
                kwarg_name=self.kwarg_name)
            self.model = event_data.content_type.model_class()

        queryset = super(EventDataLookupView, self).get_lookup_queryset()

        if hasattr(queryset, "emarsys_kwarg_name_filter"):
            queryset = queryset.emarsys_kwarg_name_filter(self.kwarg_name)

        return queryset

    def lookup_filter(self, queryset, query):
        if hasattr(queryset, 'emarsys_filter'):
            return queryset.emarsys_filter(query)
        return queryset.filter(pk=query)


class EventInstanceListView(SearchFormMixin, SearchMixin, SingleTableView):
    model = EventInstance
    table_class = EventInstanceTable
    template_name = 'dashboard/emarsys/event_instance_list.html'

    search = {
        'name': 'event__name__icontains',
        'id': 'event__emarsys_id',
    }

    search_types = {
        'id': int
    }


class EventInstanceView(DetailView):
    model = EventInstance
    context_object_name = 'event_instance'
    template_name = 'dashboard/emarsys/event_instance.html'

    def get_context_data(self, **kwargs):
        context = super(EventInstanceView, self).get_context_data(**kwargs)
        context['placeholder_data'] = sorted(json.loads(
            context['event_instance'].context)['global'].items())
        return context
