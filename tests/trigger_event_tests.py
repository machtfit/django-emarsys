# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User

from django_emarsys.event import trigger_event
from django_emarsys.models import NewEventInstance


class TriggerEventTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user, _ = User.objects.get_or_create(
            username="test_user",
            defaults=dict(email="test.user@machtfit.de"))

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_trigger_event_with_unknown_name(self, mock_api_get_events):
        mock_api_get_events.return_value = {}
        settings.EMARSYS_EVENTS = {}
        event = trigger_event("test event", "test.user@machtfit.de")
        self.assertIsNotNone(event)
        self.assertEqual(event.state, NewEventInstance.STATE_ERROR)
        self.assertEqual(event.result, "unknown event name: 'test event'")

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_trigger_event_with_nonmatching_data_args(self,
                                                      mock_api_get_events):
        mock_api_get_events.return_value = {}
        settings.EMARSYS_EVENTS = {
            'test event': {
                'extra_user': ("User", "auth.User"),
            },
        }
        event = trigger_event("test event", self.user.email,
                              data=dict(obj=self.user))
        self.assertIsNotNone(event)
        self.assertEqual(event.state, NewEventInstance.STATE_ERROR)
        self.assertEqual(event.result,
                         "expected data args ['extra_user'], got ['obj']")

    @override_settings()
    @mock.patch("django_emarsys.api.get_events")
    def test_trigger_event_with_bad_data_value(self, mock_api_get_events):
        mock_api_get_events.return_value = {}
        settings.EMARSYS_EVENTS = {
            'test event': {
                'extra_user': ("User", "auth.User"),
            },
        }
        event = trigger_event(
            "test event", self.user.email,
            data=dict(extra_user="NOT THE RIGHT OBJECT"))
        self.assertIsNotNone(event)
        self.assertEqual(event.state, NewEventInstance.STATE_ERROR)
        self.assertEqual(event.result,
                         "expected instance of 'auth.User' for "
                         "argument 'extra_user': 'NOT THE RIGHT OBJECT'")

    @override_settings()
    @mock.patch("django_emarsys.api.trigger_event")
    @mock.patch("django_emarsys.api.get_events")
    def test_trigger_automatic_event(self, mock_api_get_events,
                                     mock_api_trigger_event):
        settings.EMARSYS_EVENTS = {
            'test event': {
                'extra_user': ("User", "auth.User"),
            },
        }

        TEST_EVENT_ID = 1
        mock_api_get_events.return_value = {'test event': TEST_EVENT_ID}

        event = trigger_event("test event", self.user.email,
                              data=dict(extra_user=self.user))
        self.assertIsNotNone(event)
        self.assertEqual(event.state, NewEventInstance.STATE_SUCCESS)
        self.assertEqual(event.source, NewEventInstance.SOURCE_AUTOMATIC)
        self.assertEqual(event.emarsys_id, TEST_EVENT_ID)

        mock_api_get_events.assert_called_with()
        mock_api_trigger_event.assert_called_with(
            TEST_EVENT_ID, self.user.email, {'global': {}})

    @override_settings()
    @mock.patch("django_emarsys.api.trigger_event")
    @mock.patch("django_emarsys.api.get_events")
    def test_trigger_manual_event(self, mock_api_get_events,
                                  mock_api_trigger_event):
        settings.EMARSYS_EVENTS = {
            'test event': {
                'extra_user': ("User", "auth.User"),
            },
        }

        TEST_EVENT_ID = 1
        mock_api_get_events.return_value = {'test event': TEST_EVENT_ID}

        event = trigger_event("test event", self.user.email,
                              data=dict(extra_user=self.user),
                              manual=True)
        self.assertIsNotNone(event)
        self.assertEqual(event.state, NewEventInstance.STATE_SUCCESS)
        self.assertEqual(event.source, NewEventInstance.SOURCE_MANUAL)
        self.assertEqual(event.emarsys_id, TEST_EVENT_ID)

        mock_api_get_events.assert_called_with()
        mock_api_trigger_event.assert_called_with(
            TEST_EVENT_ID, self.user.email, {'global': {}})
