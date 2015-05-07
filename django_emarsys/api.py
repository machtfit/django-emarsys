# -*- coding: utf-8 -*-

import logging
from itertools import islice as slice, imap as map, ifilter as filter, tee

import emarsys

from django.conf import settings

log = logging.getLogger(__name__)

client = emarsys.Emarsys(settings.EMARSYS_ACCOUNT,
                         settings.EMARSYS_PASSWORD,
                         settings.EMARSYS_BASE_URI)


BATCH_SIZE = 1000


def get_events():
    response = client.call('/api/v2/event', 'GET')
    return {event['name']: int(event['id']) for event in response}


def trigger_event(event_id, email, context):
    client.call(
        '/api/v2/event/{}/trigger'.format(event_id), 'POST',
        {
            "key_id": 3,
            "external_id": email,
            "data": context
        }
    )


def create_contact(email):
    client.call('/api/v2/contact', 'POST', {"3": email})


def get_fields():
    """
    Use this to update settings.EMARSYS_FIELDS.
    """
    response = client.call('/api/v2/field', 'GET')
    return {field['name']: (field['id'], field['application_type'])
            for field in response}


def _transform_contact_data(contact):
    return {settings.EMARSYS_FIELDS[name][0]: value
            for name, value in contact.items()}


def _create_contacts(contacts):
    """
    Returns
    (number_of_successful_creates,
     {'name@domain.org': {'error_code': 'Error message'}})
    """
    assert len(contacts) <= BATCH_SIZE

    log.debug("Attempting to create {} contacts.".format(len(contacts)))

    result = client.call('/api/v2/contact', 'POST', {'contacts': contacts})

    log.debug("{} contacts created, {} contact creations failed"
              .format(len(result['ids']), len(result.get('errors', {}))))

    return len(result['ids']), result.get('errors', {})


def _update_contacts(contacts):
    """
    Returns
    (number_of_successful_updates,
     {'name@domain.org': {'error_code': 'Error message'}})
    """
    assert len(contacts) <= BATCH_SIZE

    log.debug("Attempting to update {} contacts.".format(len(contacts)))

    result = client.call('/api/v2/contact', 'PUT', {'contacts': contacts})

    log.debug("{} contacts update, {} contact updates failed"
              .format(len(result['ids']), len(result.get('errors', {}))))

    return len(result['ids']), result.get('errors', {})


def get_contact_data(email):
    return client.call('/api/v2/contact/getdata', 'POST',
                       {'keyId': '3', 'keyValues': [email]})


def sync_contacts(contacts, create_missing=True, create_only_fields=None):
    """
    contacts is a list of dictionaries like this:
        [{
            u'E-Mail': u'total-berlin-admin@total.de',
            u'Gender': 2,
            u'First Name': u'Admin',
            u'Last Name': u'von Total Berlin',
            ...
        }, ...]

    The dictionary keys are mapped to emarsys field ids using
    settings.EMARSYS_FIELDS, which can be generated with `get_fields()`.
    """

    def chunked(it, n):
        """
        From http://stackoverflow.com/a/8991553
        """
        it = iter(it)
        while True:
            chunk = tuple(slice(it, n))
            if not chunk:
                return
            yield chunk

    if not create_only_fields:
        create_only_fields = []

    total_updated = 0
    total_created = 0

    # emails of contacts that couldn't be updated because they don't exist at
    # emarsys
    missing_contacts = []

    # emails of contacts that couldn't be updated or created due to an error at
    # emarsys
    failed_contacts = []

    contacts = map(_transform_contact_data, contacts)

    # Filter contact data using whitelist
    if settings.EMARSYS_RECIPIENT_WHITELIST is not None:
        contacts = filter(lambda contact: contact[3]  # 3=email
                          in settings.EMARSYS_RECIPIENT_WHITELIST, contacts)

    update_contacts, create_contacts = tee(contacts, 2)

    # Filter out fields in create_only_fields for updating
    create_only_field_ids = [settings.EMARSYS_FIELDS[field_name][0]
                             for field_name in create_only_fields]
    update_contacts = [{k: v for k, v in contact.items()
                        if k not in create_only_field_ids}
                       for contact in update_contacts]

    # Update contacts
    for chunk_of_contacts in chunked(update_contacts, BATCH_SIZE):
        log.debug("Updating a chunk of {} users."
                  .format(len(chunk_of_contacts)))

        num_successful, errors = _update_contacts(chunk_of_contacts)
        log.debug('{} users updated, {} users errored.'
                  .format(num_successful, len(errors)))

        total_updated += num_successful

        missing_contacts.extend(email
                                for email, error_dict in errors.items()
                                if '2008' in error_dict)
        failed_contacts.extend((email, error_dict)
                               for email, error_dict in errors.items()
                               if '2008' not in error_dict)

    if create_missing:
        # Find contacts to create in original contact list
        create_contacts = filter(lambda contact: contact[3] in
                                 missing_contacts, create_contacts)

        # Create contacts
        for chunk_of_contacts in chunked(create_contacts, BATCH_SIZE):
            log.debug("Creating a chunk of {} users."
                      .format(len(chunk_of_contacts)))

            num_successful, errors = _create_contacts(chunk_of_contacts)
            log.debug('{} users created, {} users errored.'
                      .format(num_successful, len(errors)))

            total_created += num_successful

            failed_contacts.extend((email, error_dict)
                                   for email, error_dict in errors.items())

        # All contacts were either updated or the update or create failed.
        missing_contacts = []

    return total_updated, total_created, missing_contacts, failed_contacts


# Lists
# =====

def get_lists():
    """
    Get list of lists.

    Returns {'list_1_name': 'list_id',
             ...}

    Use this to set settings.EMARSYS_LISTS.
    """
    result = client.call('/api/v2/contactlist', 'GET')
    return {list['name']: list['id'] for list in result}


def create_list(name):
    """
    Create a list with the given name.

    Example:
        create_list('My list')

    Returns 'list_id'.
    """
    result = client.call('/api/v2/contactlist', 'POST',
                         {'name': name})
    return result['id']


def get_list(name):
    """
    Get ids of contacts on the list.

    Example:
        get_list('My list')

    Returns ['contact_1_id', 'contact_2_id', ...]
    """

    list_id = settings.EMARSYS_LISTS[name]
    result = client.call('/api/v2/contactlist/{}/contacts'.format(list_id),
                         'GET')
    return result


def replace_contactlist(name, emails):
    """
    Replace the contacts on the list with the given name with the contacts
    given in emails.

    Example:
        replace_contact_list('My list', ['mail1@dom.org', 'mail2@dom.org'])

    Returns (number_of_contacts_now_on_the_list,
             {'mail@dom.org': {'error_code': 'error message',
                               ...},
              ...})
    """

    list_id = settings.EMARSYS_LISTS[name]
    result = client.call('/api/v2/contactlist/{}/replace'.format(list_id),
                         'POST', {'external_ids': emails})
    return result['inserted_contacts'], result['errors']
