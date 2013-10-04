from __future__ import unicode_literals
from functools import partial
from tastypie import fields
from tastypie.resources import Resource
from tastypie.exceptions import ApiFieldError
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from .resources import GenericResource


class GenericFieldMixin(fields.ApiField):
    """
    Provides access to GenericForeignKey objects from the django content_types
    framework.
    """

    def __init__(self, to, attribute, **kwargs):
        if not isinstance(to, dict):
            raise ValueError(
                'to field must be a dictionary in GenericFieldMixin')

        if len(to) <= 0:
            raise ValueError(
                'to field must have some values')

        for k, v in to.items():
            if not issubclass(k, models.Model) or not issubclass(v, Resource):
                raise ValueError(
                    'to field must map django models to tastypie resources')

        super(GenericFieldMixin, self).__init__(to, attribute, **kwargs)

    @property
    def to_class(self):
        if self._to_class and not issubclass(GenericResource,
                                             self._to_class):
            return self._to_class
        return partial(GenericResource, resources=self.to)

    def resource_from_uri(self, fk_resource, uri,
                          request=None, related_obj=None, related_name=None):
        try:
            obj = fk_resource.get_via_uri(uri, request=request)
            fk_resource = self.get_related_resource(obj)
            return super(GenericFieldMixin, self).resource_from_uri(
                fk_resource, uri, request, related_obj, related_name)
        except ObjectDoesNotExist:
            raise ApiFieldError(
                "Could not find the provided object via resource URI '%s'."
                % uri)

    def build_related_resource(self, *args, **kwargs):
        return super(GenericFieldMixin,
                     self).build_related_resource(*args, **kwargs)


class GenericForeignKeyField(GenericFieldMixin, fields.ToOneField):
    pass


class ToManyGenericForeignKeyField(GenericFieldMixin, fields.ToManyField):
    pass
