# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from jsonfield import JSONField

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)


class EventParam:
    def __init__(self, argument, name, model):
        self.argument = argument
        self.name = name
        self.model = model

    def model_class(self):
        return apps.get_model(self.model)

    def __eq__(self, o):
        return (self.argument == o.argument and
                self.name == o.name and
                self.model == o.model)


# deprecated
@python_2_unicode_compatible
class Event(models.Model):
    emarsys_id = models.IntegerField(null=True, unique=True)
    name = models.CharField(max_length=1024, blank=True, unique=True)
    kwargs = models.ManyToManyField(ContentType, through='EventData')

    def __str__(self):
        return self.name

    class Meta:
        permissions = [('can_trigger_event', _('Can trigger emarsys events.'))]
        ordering = ['name']


# deprecated
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


# deprecated
@python_2_unicode_compatible
class EventInstance(models.Model):
    STATE_CHOICES = [('sending', 'sending'),
                     ('error', 'error'),
                     ('success', 'success')]

    SOURCE_CHOICES = [('automatic', 'automatic'),
                      ('manual', 'manual')]

    event = models.ForeignKey(Event)
    recipient_email = models.CharField(max_length=1024)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    context = models.TextField()
    data = GenericRelation('EventInstanceData')
    when = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=1024, choices=SOURCE_CHOICES)
    result = models.CharField(max_length=1024, blank=True)
    result_code = models.CharField(max_length=1024, blank=True)
    state = models.CharField(max_length=1024, choices=STATE_CHOICES,
                             default='sending')

    def __str__(self):
        return 'at {}: {}'.format(self.when, self.event.name)


# deprecated
class EventInstanceData(models.Model):
    event_trigger = models.ForeignKey(EventInstance)
    event_data = models.ForeignKey(EventData)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = [('event_trigger', 'event_data')]


# new classes

class NewEvent(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    emarsys_id = models.IntegerField()

    class Meta:
        permissions = [('can_trigger_event', _('Can trigger emarsys events.'))]
        ordering = ['name']

    def label(self):
        if self.emarsys_id:
            return ('success', "OK")
        return ('important', "Emarsys-ID unbekannt")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class NewEventInstance(models.Model):
    STATE_SENDING = "sending"
    STATE_ERROR = "error"
    STATE_SUCCESS = "success"

    SOURCE_AUTOMATIC = "automatic"
    SOURCE_MANUAL = "manual"

    STATE_CHOICES = [(STATE_SENDING, 'sending'),
                     (STATE_ERROR, 'error'),
                     (STATE_SUCCESS, 'success')]

    SOURCE_CHOICES = [(SOURCE_AUTOMATIC, 'automatic'),
                      (SOURCE_MANUAL, 'manual')]

    event_name = models.CharField(max_length=1024)
    recipient_email = models.CharField(max_length=1024)
    context = JSONField(null=True)
    data = JSONField()
    when = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=1024, choices=SOURCE_CHOICES)
    result = models.CharField(max_length=1024, blank=True)
    result_code = models.CharField(max_length=1024, blank=True)
    state = models.CharField(max_length=1024, choices=STATE_CHOICES,
                             default=STATE_SENDING)
    emarsys_id = models.IntegerField(null=True, blank=True)

    def handle_error(self, msg):
        log.error("error for event id={}: {}".format(self.id, msg))
        self.result = unicode(msg)
        self.state = NewEventInstance.STATE_ERROR
        self.save()

    def handle_emarsys_error(self, emarsys_error):
        log.error("emarsys error for event id={}: {}"
                  .format(self.id, emarsys_error))
        self.result = 'Emarsys error: {}'.format(emarsys_error)
        self.result_code = emarsys_error.code
        self.state = NewEventInstance.STATE_ERROR
        self.save()

    def handle_success(self):
        self.state = NewEventInstance.STATE_SUCCESS
        self.save()

    def label(self):
        return ({
            NewEventInstance.STATE_SENDING: 'default',
            NewEventInstance.STATE_ERROR: 'important',
            NewEventInstance.STATE_SUCCESS: 'success'}[self.state], self.state)

    def set_context(self, context):
        self.context = context
        self.save()

    def set_parameter(self, parameter, value):
        """
        Store the object passed as `value` as for the given `parameter`.

        Example:
        >>> event.set_parameter(
                EventParam(
                    argument="user",
                    name="User",
                    model="auth.User"
                ),
                value=User.objects.get(pk=1)
            )

        will store:

        >>> self.data = {
                [...]
                "user": ("User", "auth.User", 1),
                [...]
            }

        """
        if not self.data:
            self.data = {}

        self.data[parameter.argument] = (
            parameter.name,
            parameter.model,
            value.pk,
        )

        self.save()

    def get_parameter(self, argument):
        """
        Get the object stored as `argument`.

        This reads out the model and primary key of the object for
        the given `argument` and then instantiates and returns it.

        :return: (value, `EventParam`)

        """
        if not self.data:
            return None

        name, model, pk = self.data[argument]
        param = EventParam(argument=argument, name=name, model=model)
        value = param.model_class().objects.get(pk=pk)

        return value, param

    def get_all_parameters(self):
        return {argument: self.get_parameter(argument)
                for argument in self.data.keys()}

    def get_event_pk(self):
        return NewEvent.objects.get(name=self.event_name).pk

    def __str__(self):
        return 'at {}: {}'.format(self.when, self.event_name)
