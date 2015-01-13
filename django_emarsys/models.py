# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from emarsys import EmarsysError

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from oscar.core.compat import get_user_model

from . import api, managers, context_provider_registry


@python_2_unicode_compatible
class Event(models.Model):
    emarsys_id = models.IntegerField(null=True, unique=True)
    name = models.CharField(max_length=1024, blank=True, unique=True)
    kwargs = models.ManyToManyField(ContentType, through='EventData')

    def __str__(self):
        return self.name

    def trigger(self, recipient_email, user=None, data=None,
                source='automatic', async=False):
        if async:
            raise NotImplementedError

        if data is None:
            data = {}

        context = {'global': self.get_placeholder_data(
            **dict(data, user=user))}

        event_instance = self.eventinstance_set.create(
            recipient_email=recipient_email,
            context=json.dumps(context),
            user=user,
            source=source)

        name = None
        try:
            with transaction.atomic():
                for name, value in data.items():
                    event_instance.eventinstancedata_set.create(
                        event_data=self.eventdata_set.get(kwarg_name=name),
                        content_object=value)
        except (self.eventdata_set.model.DoesNotExist,
                self.eventdata_set.model.MultipleObjectsReturned) as e:
            event_instance.handle_error(
                'Programming error for event data {}: {}'
                .format(name, e))
            return event_instance

        if settings.EMARSYS_RECIPIENT_WHITELIST is not None:
            if recipient_email not in settings.EMARSYS_RECIPIENT_WHITELIST:
                event_instance.handle_error(
                    'User not on whitelist: {}'.format(recipient_email))
                return event_instance

        if not self.emarsys_id:
            event_instance.handle_error('Emarsys-ID unknown')
            return event_instance

        try:
            api.trigger_event(self.emarsys_id, recipient_email, context)
        except EmarsysError as e:
            event_instance.handle_emarsys_error(e)
            return event_instance

        event_instance.handle_success()
        return event_instance

    def get_placeholder_data(self, **kwargs):
        context_provider = context_provider_registry.get_context_provider(
            self.name)

        return context_provider(**kwargs)

    def label(self):
        if self.emarsys_id:
            return ('success', "OK")
        return ('important', "Emarsys-ID unbekannt")

    objects = managers.EventManager()

    class Meta:
        permissions = [('can_trigger_event', _('Can trigger emarsys events.'))]
        ordering = ['name']


@python_2_unicode_compatible
class EventData(models.Model):
    """
    e.eventdata_set.create(
        content_type=ContentType.objects.get_for_model(User),
        name="Benutzer",
        kwarg_name="user")
    """
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=1024)
    kwarg_name = models.CharField(max_length=1024)
    content_type = models.ForeignKey(ContentType)

    def __str__(self):
        return "({}) {}={}".format(
            self.name, self.kwarg_name, self.content_type)

    class Meta:
        unique_together = [('event', 'kwarg_name'),
                           ('event', 'name')]


@python_2_unicode_compatible
class EventInstance(models.Model):
    STATE_CHOICES = [('sending', 'sending'),
                     ('error', 'error'),
                     ('success', 'success')]

    SOURCE_CHOICES = [('automatic', 'automatic'),
                      ('manual', 'manual')]

    event = models.ForeignKey(Event)
    recipient_email = models.CharField(max_length=1024)
    user = models.ForeignKey(get_user_model(), null=True)
    context = models.TextField()
    data = GenericRelation('EventInstanceData')
    when = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=1024, choices=SOURCE_CHOICES)
    result = models.CharField(max_length=1024, blank=True)
    result_code = models.CharField(max_length=1024, blank=True)
    state = models.CharField(max_length=1024, choices=STATE_CHOICES,
                             default='sending')

    def handle_error(self, msg):
        self.result = msg
        self.state = 'error'
        self.save()

    def handle_emarsys_error(self, emarsys_error):
        self.result = 'Emarsys error: {}'.format(emarsys_error)
        self.result_code = emarsys_error.code
        self.state = 'error'
        self.save()

    def handle_success(self):
        self.state = 'success'
        self.save()

    def label(self):
        return ({
            'sending': 'default',
            'error': 'important',
            'success': 'success'}[self.state], self.state)

    def __str__(self):
        return 'at {}: {}'.format(self.when, self.event.name)


class EventInstanceData(models.Model):
    event_trigger = models.ForeignKey(EventInstance)
    event_data = models.ForeignKey(EventData)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = [('event_trigger', 'event_data')]
