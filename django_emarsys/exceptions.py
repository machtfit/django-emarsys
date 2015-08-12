# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class DjangoEmarsysError(Exception):
    pass


class BadDataError(DjangoEmarsysError):
    def __init__(self, expected_args, actual_args):
        super(BadDataError, self).__init__(
            "expected data args {}, got {}"
            .format([unicode(x).encode() for x in expected_args],
                    [unicode(x).encode() for x in actual_args]))


class UnknownEventNameError(DjangoEmarsysError):
    def __init__(self, name):
        super(UnknownEventNameError, self).__init__("unknown event name: '{}'"
                                                    .format(name))
