# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User

from django_emarsys.models import NewEventInstance
from django_emarsys.event import EventParam


class ModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create(username="test_user",
                                       email="test.user@machtfit.de")
        cls.event = NewEventInstance.objects.create(event_name='foobar')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.event.delete()

    def test_set_and_get_parameter(self):
        param = EventParam(argument='user', name='User', model='auth.User')
        self.event.set_parameter(param, self.user)
        value, restored_param = self.event.get_parameter('user')
        self.assertEqual(value, self.user)
        self.assertEqual(restored_param, param)
