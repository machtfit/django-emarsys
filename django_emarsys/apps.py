from django.apps import AppConfig
from django.core.checks import register

from .config import validate_settings


class DjangoEmarsysConfig(AppConfig):
    name = 'django_emarsys'
    verbose_name = "Django Emarsys"

    def ready(self):
        @register()
        def check_settings(app_configs):
            messages = validate_settings()
            for message in messages:
                # apparently Django's check framework can't handle
                # unicode correctly, so replace all non-ascii characters
                # with '?'
                message.msg = message.msg.encode('ascii', 'replace')

            return messages
