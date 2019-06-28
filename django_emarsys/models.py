import logging

from jsonfield import JSONField

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from django_emarsys import EventParam

log = logging.getLogger(__name__)


@python_2_unicode_compatible
class Event(models.Model):
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
class EventInstance(models.Model):
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
        log.warning("error for event id={}: {}".format(self.id, msg))
        self.result = str(msg)
        self.state = EventInstance.STATE_ERROR
        self.save()

    def handle_emarsys_error(self, emarsys_error):
        log.warning("emarsys error for event id={}: {}"
                  .format(self.id, emarsys_error))
        self.result = 'Emarsys error: {}'.format(emarsys_error)
        self.result_code = emarsys_error.code
        self.state = EventInstance.STATE_ERROR
        self.save()

    def handle_success(self):
        self.state = EventInstance.STATE_SUCCESS
        self.save()

    def label(self):
        return ({
            EventInstance.STATE_SENDING: 'default',
            EventInstance.STATE_ERROR: 'important',
            EventInstance.STATE_SUCCESS: 'success'}[self.state], self.state)

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
                    type_="auth.User"
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

        if parameter.is_string:
            pk = value
        elif parameter.is_list:
            pk = [x.pk for x in value]
        else:
            pk = value.pk

        self.data[parameter.argument] = (
            parameter.name,
            parameter.type_,
            pk,
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

        name, type_, pk = self.data[argument]
        param = EventParam(argument=argument, name=name, type_=type_)
        if param.is_string:
            value = pk
        elif param.is_list:
            value = param.model_class().objects.filter(pk__in=pk)
        else:
            try:
                value = param.model_class().objects.get(pk=pk)
            except param.model_class().DoesNotExist:
                value = None

        return value, param

    def get_all_parameters(self):
        if self.data:
            return {argument: self.get_parameter(argument)
                    for argument in self.data.keys()}
        return {}

    def get_event_pk(self):
        return Event.objects.get(name=self.event_name).pk

    def __str__(self):
        return 'at {}: {}'.format(self.when, self.event_name)
