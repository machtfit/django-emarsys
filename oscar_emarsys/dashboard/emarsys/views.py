# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from emarsys import EmarsysError

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import Form
from django.utils.http import urlencode
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.edit import FormView

from django_tables2 import SingleTableView

from oscar.views.generic import ObjectLookupView

from apps.views import SearchMixin, SearchFormMixin

from django_emarsys.models import NewEvent, NewEventInstance
from django_emarsys.context_provider_registry import ContextProviderException
from django_emarsys.event import (get_parameter_for_event,
                                  get_placeholder_data,
                                  trigger_event, sync_events)

from .forms import EventTriggerForm
from .tables import EventTable, EventInstanceTable


class EventListView(SearchFormMixin, SearchMixin, SingleTableView):
    model = NewEvent
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
            sync_events()
            messages.success(self.request, 'Events gesynct.')
        except EmarsysError as e:
            messages.error(self.request, 'Emarsys error: {}'.format(e))
        return super(EventsSyncView, self).form_valid(form)

    def get_success_url(self):
        return "{}?{}".format(reverse('dashboard:emarsys-event-list'),
                              urlencode(self.request.GET, doseq=True))


class EventTriggerMixin(object):
    model = NewEvent
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
            data = get_placeholder_data(self.event.name, **form.cleaned_data)
            context['placeholder_data'] = sorted(data.items())
        return context

    def form_valid(self, form):
        recipient_email = form.cleaned_data.pop('recipient_email')

        event_instance = trigger_event(
            event_name=self.event.name,
            recipient_email=recipient_email,
            data=form.cleaned_data,
            manual=True)

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
                data = get_placeholder_data(self.event.name,
                                            **form.cleaned_data)
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
        self.argument = kwargs.pop('argument')
        return super(EventDataLookupView, self).get(*args, **kwargs)

    def get_lookup_queryset(self):
        self.model = get_parameter_for_event(
            self.event.name, self.argument).model_class()

        queryset = super(EventDataLookupView, self).get_lookup_queryset()

        if hasattr(queryset, "emarsys_kwarg_name_filter"):
            queryset = queryset.emarsys_kwarg_name_filter(self.argument)

        return queryset

    def format_object(self, obj):
        if not hasattr(obj, 'emarsys_format'):
            return super(EventDataLookupView, self).format_object(obj)

        return {
            'id': obj.pk,
            'text': obj.emarsys_format
        }

    def lookup_filter(self, queryset, query):
        if hasattr(queryset, 'emarsys_filter'):
            return queryset.emarsys_filter(query)
        return queryset.filter(pk=query)


class EventInstanceListView(SearchFormMixin, SearchMixin, SingleTableView):
    model = NewEventInstance
    table_class = EventInstanceTable
    template_name = 'dashboard/emarsys/event_instance_list.html'

    search = {
        'email': 'recipient_email__icontains',
        'event': 'event_name__icontains',
        'id': 'emarsys_id',
    }

    search_types = {
        'id': int
    }


class EventInstanceView(DetailView):
    model = NewEventInstance
    context_object_name = 'event_instance'
    template_name = 'dashboard/emarsys/event_instance.html'

    def get_context_data(self, **kwargs):
        context = super(EventInstanceView, self).get_context_data(**kwargs)
        context['placeholder_data'] = sorted(
            context['event_instance'].context['global'].items())
        return context
