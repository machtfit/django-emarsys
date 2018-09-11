# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django.apps

default_app_config = 'django_emarsys.apps.DjangoEmarsysConfig'


class EventParam(object):
    def __init__(self, argument, name, type_):
        self.argument = argument
        self.name = name
        self.type_ = unicode(type_)

        self.is_list = self.type_[0] == '[' and self.type_[-1] == ']'

        self.is_string = self.type_ == 'string'

        if self.is_list:
            self.model = self.type_[1:-1]
        else:
            self.model = self.type_

    def model_class(self):
        return django.apps.apps.get_model(self.model)

    def __eq__(self, o):
        return (self.argument == o.argument and
                self.name == o.name and
                self.type_ == o.type_)
