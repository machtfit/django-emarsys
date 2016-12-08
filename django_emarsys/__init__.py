# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django.apps

default_app_config = 'django_emarsys.apps.DjangoEmarsysConfig'


class EventParam:
    def __init__(self, argument, name, type_):
        self.argument = argument
        self.name = name
        self.type_ = type_

        self.is_list = type_[0] == '[' and type_[-1] == ']'

        if self.is_list:
            self.model = type_[1:-1]
        else:
            self.model = type_

    def model_class(self):
        return django.apps.apps.get_model(self.model)

    def __eq__(self, o):
        return (self.argument == o.argument and
                self.name == o.name and
                self.type_ == o.type_)
