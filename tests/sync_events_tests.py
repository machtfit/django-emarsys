import mock

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from django_emarsys.event import sync_events
from django_emarsys.models import Event


class SyncEventTestCase(TestCase):
    @classmethod
    def setUp(self):
        Event.objects.all()

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_num_new_events(self, mock_api_get_events):
        mock_api_get_events.return_value = {
            'töst event 1': 1,
            'töst event 2': 2,
        }
        settings.EMARSYS_EVENTS = {
            'töst event 1': {
            },
            'töst event 2': {
            },
        }
        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(num_new_events, 2)
        self.assertEqual(
            Event.objects.get(name='töst event 1').emarsys_id, 1)
        self.assertEqual(
            Event.objects.get(name='töst event 2').emarsys_id, 2)

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_num_updated_events(self, mock_api_get_events):
        mock_api_get_events.return_value = {
            'töst event 1': 1,
            'töst event 2': 2,
        }
        settings.EMARSYS_EVENTS = {
            'töst event 1': {
            },
            'töst event 2': {
            },
        }

        Event.objects.create(name='töst event 1', emarsys_id=1)
        # this one will be updated to 2
        Event.objects.create(name='töst event 2', emarsys_id=3)

        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(num_updated_ids, 1)
        self.assertEqual(
            Event.objects.get(name='töst event 1').emarsys_id, 1)
        self.assertEqual(
            Event.objects.get(name='töst event 2').emarsys_id, 2)

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_num_deleted_events(self, mock_api_get_events):
        mock_api_get_events.return_value = {
        }
        settings.EMARSYS_EVENTS = {
        }

        Event.objects.create(name='töst event 1', emarsys_id=1)

        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(num_deleted_ids, 1)
        self.assertEqual(Event.objects.all().count(), 0)

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_num_deleted_unknown_events(self, mock_api_get_events):
        EVENT_NAME = 'unknown event näme'
        mock_api_get_events.return_value = {
            EVENT_NAME: 1,
        }
        settings.EMARSYS_EVENTS = {
        }

        Event.objects.create(name=EVENT_NAME, emarsys_id=1)

        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(num_deleted_ids, 1)
        self.assertEqual(Event.objects.all().count(), 0)

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_unknown_event_names(self, mock_api_get_events):
        EVENT_NAME = 'unknown event näme'
        mock_api_get_events.return_value = {
            EVENT_NAME: 1,
        }
        settings.EMARSYS_EVENTS = {
        }

        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(Event.objects.all().count(), 0)

    @override_settings()
    @mock.patch("django_emarsys.event.log")
    @mock.patch("django_emarsys.api.get_events")
    def test_sync_events_unsynced_event_names(self, mock_api_get_events,
                                              mock_event_log):
        mock_api_get_events.return_value = {
        }
        settings.EMARSYS_EVENTS = {
            'unsynced event näme': {},
        }

        num_new_events, num_updated_ids, num_deleted_ids, \
            unsynced_event_names = sync_events()

        self.assertEqual(unsynced_event_names, ['unsynced event näme'])
        mock_event_log.warning.assert_called_with(
            'these event names in settings.EMARSYS_EVENTS '
            'are not known by Emarsys: "unsynced event näme"')
