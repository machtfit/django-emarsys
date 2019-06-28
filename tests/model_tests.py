from django.test import TestCase
from django.contrib.auth.models import User

from django_emarsys.models import EventInstance
from django_emarsys import EventParam


class ModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create(username="test_user",
                                       email="test.user@machtfit.de")
        cls.event = EventInstance.objects.create(event_name='foobar')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.event.delete()

    def test_set_and_get_parameter(self):
        param = EventParam(argument='user', name='User', type_='auth.User')
        self.event.set_parameter(param, self.user)
        value, restored_param = self.event.get_parameter('user')
        self.assertEqual(value, self.user)
        self.assertEqual(restored_param, param)
