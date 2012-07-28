# See COPYING file in this directory.
# Some code originally from django-boundaryservice

from urllib import unquote

from django.contrib.gis.db.models import GeometryField
from django.utils import simplejson
from django.contrib.gis.geos import GEOSGeometry

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

        if value and isinstance(value, GEOSGeometry):
            return value.geojson

        if isinstance(value, dict):
            return simplejson.dumps(value)

    def to_geom(self, s):
        try:
            return GEOSGeometry(unquote(s))
        except ValueError:
            return None

    def dehydrate(self, obj):
        v = self.convert(super(GeometryApiField, self).dehydrate(obj))
        if v:
            return simplejson.loads(v.geojson)

    def convert(self, value):
        if isinstance(value, basestring):
            return self.to_geom(value)
        return value


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
