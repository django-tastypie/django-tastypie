# See COPYING file in this directory.
# Some code originally from django-boundaryservice
from urllib import unquote

from django.utils import simplejson
from django.contrib.gis.measure import D
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models import GeometryField

from tastypie import resources
from tastypie.fields import ApiField, CharField

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

    def filter_value_to_python(self, value, field_name, filters, filter_expr,
            filter_type):
        value = super(ModelResource, self).filter_value_to_python(
            value, field_name, filters, filter_expr, filter_type)

        # If we are filtering on a GeometryApiField then we should try
        # and convert this to a GEOSGeometry object.  The conversion
        # will fail if we don't have value JSON, so in that case we'll
        # just return ``value`` as normal.
        if isinstance(self.fields[field_name], GeometryApiField):
            try:
                value = GEOSGeometry(unquote(value))
            except ValueError:
                pass
            else:
                # Check if is a Distance Query operator,
                # and if so interpolate distance radius
                if filter_type.startswith('distance_'):
                    try:
                        radius = filters['distance.radius']
                        units = filters['distance.units']
                        value = (value, D(**{units: radius}))
                    except (KeyError, ValueError):
                        raise
                elif filter_type == 'dwithin':
                    # e.g PostGIS ST_DWIthin query
                    try:
                        radius = float(filters['distance.radius'])
                        value = (value, radius)
                    except:
                        raise
        return value
