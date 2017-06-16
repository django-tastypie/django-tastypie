import datetime
import logging
import six

from tastypie import fields


class SimpleHandler(logging.Handler):
    logged = []

    def emit(self, record):
        SimpleHandler.logged.append(record)


def adjust_schema(schema_dict):
    for field, field_info in schema_dict['fields'].items():
        if isinstance(field_info['default'], six.string_types) and field_info['type'] in ('datetime', 'date',):
            field_info['default'] = 'The current date.'
        if isinstance(field_info['default'], (datetime.datetime, datetime.date)):
            field_info['default'] = 'The current date.'
        if isinstance(field_info['default'], fields.NOT_PROVIDED):
            field_info['default'] = 'No default provided.'
    return schema_dict
