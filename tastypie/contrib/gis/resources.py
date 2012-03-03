# See COPYING file in this directory.
# Originally from django-boundaryservice

from django.contrib.gis.db.models import GeometryField
from django.utils import simplejson

from tastypie.fields import ApiField, CharField
from tastypie import resources


class GeometryApiField(ApiField):
    """
    Custom ApiField for dealing with data from GeometryFields (by serializing
    them as GeoJSON).
    """
    dehydrated_type = 'geometry'
    help_text = 'Geometry data.'

    def hydrate(self, bundle):
        value = super(GeometryApiField, self).hydrate(bundle)
        if value is None:
            return value
        return simplejson.dumps(value)

    def dehydrate(self, obj):
        return self.convert(super(GeometryApiField, self).dehydrate(obj))

    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        # Get ready-made geojson serialization and then convert it _back_ to
        # a Python object so that tastypie can serialize it as part of the
        # bundle.
        return simplejson.loads(value.geojson)


class ModelResource(resources.ModelResource):
    """
    ModelResource subclass that handles geometry fields as GeoJSON.
    """
    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        """
        Overrides default field handling to support custom GeometryApiField.
        """
        if isinstance(f, GeometryField):
            return GeometryApiField

        return super(ModelResource, cls).api_field_from_django_field(f, default)
