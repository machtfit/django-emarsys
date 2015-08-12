# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock

from django.conf import settings
from django.core.checks import Critical, Error, Warning
from django.test import TestCase
from django.test.utils import override_settings

from django_emarsys import config


def _make_message_set(messages):
    """
    Unfortunately `django.core.checks.CheckMessage` doesn't implement
    `__hash__()`, so sets containing them cannot be compared directly.
    As a workaround this makes a set containing tuples of the level
    and message, which are the only two attributes the tests care about.

    Example:
    >>> from django.core.checks import Critical
    >>> c1 = Critical("foobar")
    >>> c2 = Critical("foobar")
    >>> c1 == c2
    True
    >>> {c1} == {c2}
    False
    >>> _make_message_set({c1}) == _make_message_set({c2})
    True

    """
    return {(m.level, m.msg) for m in messages}


class ConfigurationTestCase(TestCase):
    def test_configuration_present(self):
        """
        Make sure there's an error if any of the needed EMARSYS_
        settings is missing.

        """
        configuration = {}
        messages = config.validate_configuration(configuration)

        self.assertSetEqual(
            _make_message_set(messages),
            _make_message_set([
                Critical('EMARSYS_ACCOUNT not set'),
                Critical('EMARSYS_PASSWORD not set'),
                Critical('EMARSYS_BASE_URI not set'),
                Critical('EMARSYS_EVENTS not set')]))

    def test_emarsys_events_not_empty(self):
        """
        Make sure there's a warning if no Emarsys events are configured.

        """
        configuration = {
            'EMARSYS_ACCOUNT': 'account',
            'EMARSYS_PASSWORD': 'password',
            'EMARSYS_BASE_URI': 'base_uri',
            'EMARSYS_EVENTS': {}
        }
        messages = config.validate_configuration(configuration)

        self.assertSetEqual(
            _make_message_set(messages),
            _make_message_set([Warning('EMARSYS_EVENTS is empty')]))

    def test_configuration_integrity(self):
        """
        Make sure malformed `EMARSYS_EVENTS` settings will result
        in the right check error messages.

        See `django_emarsys.config.validate_configuration` for the
        expected structure.

        """
        configuration = {
            'EMARSYS_ACCOUNT': 'account',
            'EMARSYS_PASSWORD': 'password',
            'EMARSYS_BASE_URI': 'base_uri',
            'EMARSYS_EVENTS': {
                '': [],
                'test event 1': {
                    'reused_arg': ("Reused", "auth.User"),
                    'arg': ("Reused", "auth.User"),
                    '': ("foobar", "auth.User"),
                    'invalid arg': ("", "auth.User"),
                    'not_reused_arg': ("Not Reused Name", "auth.User"),
                },
                'test event 2': {
                    'not_reused_arg': ("Not Reused Name", "auth.User"),
                },
                'test event 3': {
                    'user1': ("User1", "invalid_app.User"),
                    'user2': ("User2", "auth.InvalidModel"),
                    'user3': ("User3", "foo.bar.User"),
                    'user4': ("User4", "User"),
                    'user5': (),
                    'user6': (1, "auth.User"),
                    'user7': ("User7", 1),
                    'user8': "foo",
                },
                'töst üvänt,.!?;-#+* ß': {
                    'üser': ("Üser", "auth.User"),
                },
            },
        }

        messages = config.validate_configuration(configuration)

        self.assertSetEqual(
            _make_message_set(messages),
            _make_message_set([
                Error("invalid parameter name for event 'test event 1': ''"),
                Error("invalid parameter argument for event 'test event 1': ''"),  # noqa
                Error("invalid parameter argument for event 'test event 1': 'invalid arg'"),  # noqa
                Error("bad model 'invalid_app.User' for event 'test event 3': No installed app with label 'invalid_app'."),  # noqa
                Error("bad model 'auth.InvalidModel' for event 'test event 3': App 'auth' doesn't have a 'invalidmodel' model."),  # noqa
                Error("bad model 'foo.bar.User' for event 'test event 3': too many values to unpack"),  # noqa
                Error("bad model 'User' for event 'test event 3': need more than 1 value to unpack"),  # noqa
                Error("invalid parameter definition 'test event 3': 'user5' => ()"),  # noqa
                Error("bad model '1' for event 'test event 3': 'int' object has no attribute 'split'"),  # noqa
                Error("invalid parameter name for event 'test event 3': '1'"),
                Error("invalid parameter definition 'test event 3': 'user8' => foo"),  # noqa
                Error("invalid parameter argument for event 'töst üvänt,.!?;-#+* ß': 'üser'"),  # noqa

                Warning("invalid event name: ''"),
                Warning("reused parameter name for event 'test event 1': 'Reused'"),  # noqa
            ]))

    @override_settings()
    @mock.patch('django_emarsys.config.validate_configuration')
    def test_validate_settings(self, mock_validate_configuration):
        """
        Make sure `validate_settings` correctly passes the actual settings
        as a dict to `validate_configuration`, which does all the work
        and was tested above.

        """
        expected_config = {key: getattr(settings, key)
                           for key in dir(settings)
                           if hasattr(settings, key)}
        config.validate_settings()

        mock_validate_configuration.assert_called_with(expected_config)
