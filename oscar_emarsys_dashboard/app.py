# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url

from oscar.core.application import Application

from . import views


class EmarsysDashboardApplication(Application):
    default_permissions = (['django_emarsys.can_trigger_event'])

    event_list_view = views.EventListView
    events_sync_view = views.EventsSyncView
    event_trigger_view = views.EventTriggerView
    event_data_lookup_view = views.EventDataLookupView
    event_placeholder_data_view = views.EventPlaceholderDataView
    event_instance_list_view = views.EventInstanceListView
    event_instance_view = views.EventInstanceView

    def get_urls(self):
        urls = [
            url(r'^$', self.event_list_view.as_view(),
                name='emarsys-event-list'),
            url(r'^sync/$', self.events_sync_view.as_view(),
                name='emarsys-events-sync'),
            url(r'^(?P<pk>\d+)/trigger/$', self.event_trigger_view.as_view(),
                name='emarsys-event-trigger'),
            url(r'^(?P<pk>\d+)/lookup/(?P<name>[^/]+)/$',
                self.event_data_lookup_view.as_view(),
                name='emarsys-event-data-lookup'),
            url(r'^(?P<pk>\d+)/placeholder-data/$',
                self.event_placeholder_data_view.as_view(),
                name='emarsys-event-placeholder-data'),
            url(r'^instances/$', self.event_instance_list_view.as_view(),
                name='emarsys-event-instance-list'),
            url(r'^instances/(?P<pk>\d+)/$',
                self.event_instance_view.as_view(),
                name='emarsys-event-instance')
        ]
        return self.post_process_urls(urls)

application = EmarsysDashboardApplication()
