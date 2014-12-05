# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from django_tables2 import A, LinkColumn, Column

from oscar.core.loading import get_class

from django_emarsys.models import Event, EventInstance

DashboardTable = get_class('dashboard.tables', 'DashboardTable')


class LabelColumn(Column):
    def render(self, value):
        label, text = value
        return mark_safe('<span class="label label-{label}">{text}</span>'
                         .format(label=label, text=text))


class EventTable(DashboardTable):
    name = LinkColumn('dashboard:emarsys-event-trigger',
                      verbose_name=_('Name'), args=[A('pk')])
    state = LabelColumn(accessor='label', order_by='emarsys_id')

    icon = 'envelope'
    caption_singular = "{count} Event"
    caption_plural = "{count} Events"

    class Meta(DashboardTable.Meta):
        model = Event
        fields = ()
        template = 'dashboard/emarsys/event_table.html'


class EventInstanceTable(DashboardTable):
    when = LinkColumn('dashboard:emarsys-event-instance',
                      args=[A('pk')])
    state = LabelColumn(accessor='label', order_by='emarsys_id')

    icon = 'envelope'
    caption_singular = "{count} Event Instance"
    caption_plural = "{count} Event Instances"

    class Meta(DashboardTable.Meta):
        model = EventInstance
        fields = ('when', 'event', 'source', 'result', 'state')
