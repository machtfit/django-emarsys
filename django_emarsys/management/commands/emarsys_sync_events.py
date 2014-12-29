# -*- coding: utf-8 -*-

from django.core.management import BaseCommand

from ...models import Event


class Command(BaseCommand):
    def handle(self, *args, **options):
        num_new_events, num_added_ids, num_updated_ids, num_deleted_ids \
            = Event.objects.sync_events()
        print("{} new events, {} event ids added, {} event ids updated,"
              " {} event ids deleted"
              .format(num_new_events, num_added_ids, num_updated_ids,
                      num_deleted_ids))
