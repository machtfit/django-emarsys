# -*- coding: utf-8 -*-

from __future__ import unicode_literals


from django.contrib import admin

from .models import Event, EventData


class EventDataInline(admin.TabularInline):
    model = EventData


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'emarsys_id')
    inlines = [EventDataInline]
