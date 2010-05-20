from dateutil.parser import parse
import re
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.utils import datetime_safe
from tastypie.bundle import Bundle
from tastypie.exceptions import ApiFieldError


class NOT_PROVIDED:
    pass


DATE_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).*?$')
DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).*?$')


# All the ApiField variants.

class ApiField(object):
    """The base implementation of a field used by the resources."""
    dehydrated_type = 'string'
    
    def __init__(self, attribute=None, default=NOT_PROVIDED, null=False, readonly=False):
        """
        Sets up the field. This is generally called when the containing
        ``Resource`` is initialized.
        
        Optionally accepts an ``attribute``, which should be a string of
        either an instance attribute or callable off the object during the
        ``dehydrate`` or push data onto an object during the ``hydrate``.
        Defaults to ``None``, meaning data will be manually accessed.
        
        Optionally accepts a ``default``, which provides default data when the
        object being ``dehydrated``/``hydrated`` has no data on the field.
        Defaults to ``NOT_PROVIDED``.
        
        Optionally accepts a ``null``, which indicated whether or not a
        ``None`` is allowable data on the field. Defaults to ``False``.
        
        Optionally accepts a ``readonly``, which indicates whether the field
        is used during the ``hydrate`` or not. Defaults to ``False``.
        """
        # Track what the index thinks this field is called.
        self.instance_name = None
        self.attribute = attribute
        self._default = default
        self.null = null
        self.readonly = readonly
        self.value = None
    
    def has_default(self):
        """Returns a boolean of whether this field has a default value."""
        return self._default is not NOT_PROVIDED
    
    @property
    def default(self):
        """Returns the default value for the field."""
        if callable(self._default):
            return self._default()
        
        return self._default
    
    def dehydrate(self, bundle):
        """
        Takes data from the provided object and prepares it for the
        resource.
        """
        if self.attribute is not None:
            # Check for `__` in the field for looking through the relation.
            attrs = self.attribute.split('__')
            current_object = bundle.obj
            
            for attr in attrs:
                current_object = getattr(current_object, attr, None)
                
                if current_object is None:
                    if self.has_default():
                        current_object = self._default
                        # Fall out of the loop, given any further attempts at
                        # accesses will fail misreably.
                        break
                    elif self.null:
                        current_object = None
                        # Fall out of the loop, given any further attempts at
                        # accesses will fail misreably.
                        break
                    else:
                        raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a default or null value." % (current_object, attr))
            
            if callable(current_object):
                return current_object()
            
            return current_object
        
        if self.has_default():
            return self.default
        else:
            return None
    
    def convert(self, value):
        """
        Handles conversion between the data found and the type of the field.
        
        Extending classes should override this method and provide correct
        data coercion.
        """
        return value
    
    def hydrate(self, bundle):
        """
        Takes data stored in the bundle for the field and returns it. Used for
        taking simple data and building a instance object.
        """
        if self.readonly:
            return None
        
        if bundle.data.get(self.instance_name) is None:
            if self.has_default():
                if callable(self._default):
                    return self._default()
                
                return self._default
            elif self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a default or null value." % self.instance_name)
        
        return bundle.data[self.instance_name]


class CharField(ApiField):
    """
    A text field of arbitrary length.
    
    Covers both ``models.CharField`` and ``models.TextField``.
    """
    dehydrated_type = 'string'
    
    def dehydrate(self, obj):
        return self.convert(super(CharField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return unicode(value)


class FileField(ApiField):
    """
    A file-related field.
    
    Covers both ``models.FileField`` and ``models.ImageField``.
    """
    dehydrated_type = 'string'
    
    def dehydrate(self, obj):
        media_url = settings.MEDIA_URL
        path = self.convert(super(FileField, self).dehydrate(obj))
        
        if path:
            media_url = media_url.rstrip('/')
            path = path.lstrip('/')
            return u"%s/%s" % (media_url, path)
        
        return path
    
    def convert(self, value):
        if value is None:
            return None
        
        return unicode(value)


class IntegerField(ApiField):
    """
    An integer field.
    
    Covers ``models.IntegerField``, ``models.PositiveIntegerField``,
    ``models.PositiveSmallIntegerField`` and ``models.SmallIntegerField``.
    """
    dehydrated_type = 'integer'
    
    def dehydrate(self, obj):
        return self.convert(super(IntegerField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return int(value)


class FloatField(ApiField):
    """
    A floating point field.
    """
    dehydrated_type = 'float'
    
    def dehydrate(self, obj):
        return self.convert(super(FloatField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return float(value)


class BooleanField(ApiField):
    """
    A boolean field.
    
    Covers both ``models.BooleanField`` and ``models.NullBooleanField``.
    """
    dehydrated_type = 'boolean'
    
    def dehydrate(self, obj):
        return self.convert(super(BooleanField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return bool(value)


class DateField(ApiField):
    """
    A date field.
    """
    dehydrated_type = 'date'
    
    def dehydrate(self, obj):
        return self.convert(super(DateField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        if isinstance(value, basestring):
            match = DATE_REGEX.search(value)
            
            if match:
                data = match.groupdict()
                return datetime_safe.date(int(data['year']), int(data['month']), int(data['day']))
            else:
                raise ApiFieldError("Date provided to '%s' field doesn't appear to be a valid date string: '%s'" % (self.instance_name, value))
        
        return value
    
    def hydrate(self, bundle):
        value = super(DateField, self).hydrate(bundle)
        
        if value and not hasattr(value, 'year'):
            try:
                # Try to rip a date/datetime out of it.
                value = parse(value)
                
                if hasattr(value, 'hour'):
                    value = value.date()
            except ValueError:
                pass
        
        return value


class DateTimeField(ApiField):
    """
    A datetime field.
    """
    dehydrated_type = 'datetime'
    
    def dehydrate(self, obj):
        return self.convert(super(DateTimeField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        if isinstance(value, basestring):
            match = DATETIME_REGEX.search(value)
            
            if match:
                data = match.groupdict()
                return datetime_safe.datetime(int(data['year']), int(data['month']), int(data['day']), int(data['hour']), int(data['minute']), int(data['second']))
            else:
                raise ApiFieldError("Datetime provided to '%s' field doesn't appear to be a valid datetime string: '%s'" % (self.instance_name, value))
        
        return value
    
    def hydrate(self, bundle):
        value = super(DateTimeField, self).hydrate(bundle)
        
        if value and not hasattr(value, 'year'):
            try:
                # Try to rip a date/datetime out of it.
                value = parse(value)
            except ValueError:
                pass
        
        return value


class RelatedField(ApiField):
    """
    Provides access to data that is related within the database.
    
    A base class not intended for direct use but provides functionality that
    ``ForeignKey`` and ``ManyToManyField`` build upon.
    
    The contents of this field actually point to another ``Resource``,
    rather than the related object. This allows the field to represent its data
    in different ways.
    
    The abstractions based around this are "leaky" in that, unlike the other
    fields provided by ``tastypie``, these fields don't handle arbitrary objects
    very well. The subclasses use Django's ORM layer to make things go, though
    there is no ORM-specific code at this level.
    """
    dehydrated_type = 'related'
    is_related = True
    self_referential = False
    
    def __init__(self, to, attribute, related_name=None, null=False, full=False):
        """
        Builds the field and prepares it to access to related data.
        
        The ``to`` argument should point to a ``Resource`` class, NOT
        to a ``Model``. Required.
        
        The ``attribute`` argument should specify what field/callable points to
        the related data on the instance object. Required.
        
        Optionally accepts a ``related_name`` argument. Currently unused, as
        unlike Django's ORM layer, reverse relations between ``Resource``
        classes are not automatically created. Defaults to ``None``.
        
        Optionally accepts a ``null``, which indicated whether or not a
        ``None`` is allowable data on the field. Defaults to ``False``.
        
        Optionally accepts a ``full``, which indicates how the related
        ``Resource`` will appear post-``dehydrate``. If ``False``, the
        related ``Resource`` will appear as a URL to the endpoint of that
        resource. If ``True``, the result of the sub-resource's
        ``dehydrate`` will be included in full.
        """
        self.instance_name = None
        self.to = to
        self.attribute = attribute
        self.related_name = related_name
        self.null = null
        self.full = full
        self.readonly = False
        self.api_name = None
        self.resource_name = None
        
        if self.to == 'self':
            self.self_referential = True
    
    def has_default(self):
        """
        Always returns ``False``, as there is no ``default`` available on
        related fields.
        """
        return False
    
    @property
    def default(self):
        """
        Raises an exception because related fields do not have a ``default``.
        """
        raise ApiFieldError("%r fields do not have default data." % self)
    
    def get_related_resource(self, related_instance):
        """
        Instaniates the related resource.
        """
        related_resource = self.to()
        # Try to be efficient about DB queries.
        related_resource.instance = related_instance
        return related_resource
    
    def dehydrate_related(self, bundle, related_resource):
        """
        Based on the ``full_resource``, returns either the endpoint or the data
        from ``full_dehydrate`` for the related resource.
        """
        if not self.full:
            # Be a good netizen.
            return related_resource.get_resource_uri(bundle)
        else:
            # ZOMG extra data and big payloads.
            return related_resource.full_dehydrate(related_resource.instance)
    
    def build_related_resource(self, value):
        """
        Used to ``hydrate`` the data provided. If just a URL is provided,
        the related resource is attempted to be loaded. If a
        dictionary-like structure is provided, a fresh resource is
        created.
        """
        self.fk_resource = self.to()
        
        if isinstance(value, basestring):
            # We got a URI. Load the object and assign it.
            try:
                obj = self.fk_resource.get_via_uri(value)
                return self.fk_resource.full_dehydrate(obj)
            except ObjectDoesNotExist:
                raise ApiFieldError("Could not find the provided object via resource URI '%s'." % value)
        elif hasattr(value, 'items'):
            # Try to hydrate the data provided.
            self.fk_bundle = Bundle(data=value)
            return self.fk_resource.full_hydrate(self.fk_bundle)
        else:
            raise ApiFieldError("The '%s' field has was given data that was not a URI and not a dictionary-alike: %s." % (self.instance_name, value))


class ToOneField(RelatedField):
    """
    Provides access to related data via foreign key.
    
    This subclass requires Django's ORM layer to work properly.
    """
    def __init__(self, to, attribute, related_name=None, null=False, full=False):
        super(ToOneField, self).__init__(to, attribute, related_name, null=null, full=full)
        self.fk_resource = None
    
    def dehydrate(self, bundle):
        if not getattr(bundle.obj, self.attribute):
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (bundle.obj, self.attribute))
            
            return None
        
        fk = getattr(bundle.obj, self.attribute)
        self.fk_resource = self.get_related_resource(getattr(bundle.obj, self.attribute))
        fk_bundle = Bundle(obj=fk)
        return self.dehydrate_related(fk_bundle, self.fk_resource)
    
    def hydrate(self, bundle):
        if bundle.data.get(self.instance_name) is None:
            if self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a null value." % self.instance_name)
        
        return self.build_related_resource(bundle.data.get(self.instance_name))


class ForeignKey(ToOneField):
    pass


class OneToOneField(ToOneField):
    pass


class ToManyField(RelatedField):
    """
    Provides access to related data via a join table.
    
    This subclass requires Django's ORM layer to work properly.
    
    Note that the ``hydrate`` portions of this field are quite different than
    any other field. ``hydrate_m2m`` actually handles the data and relations.
    This is due to the way Django implements M2M relationships.
    """
    is_m2m = True
    
    def __init__(self, to, attribute, related_name=None, null=False, full=False):
        super(ToManyField, self).__init__(to, attribute, related_name, null=null, full=full)
        self.m2m_bundles = []
    
    def dehydrate(self, bundle):
        if not bundle.obj or not bundle.obj.pk:
            if not self.null:
                raise ApiFieldError("The model '%r' does not have a primary key and can not be used in a ToMany context." % bundle.obj)
            
            return []
        
        if not getattr(bundle.obj, self.attribute):
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (bundle.obj, self.attribute))
            
            return []
        
        self.m2m_resources = []
        m2m_dehydrated = []
        
        # TODO: Also model-specific and leaky. Relies on there being a
        #       ``Manager`` there.
        for m2m in getattr(bundle.obj, self.attribute).all():
            m2m_resource = self.get_related_resource(m2m)
            m2m_bundle = Bundle(obj=m2m)
            self.m2m_resources.append(m2m_resource)
            m2m_dehydrated.append(self.dehydrate_related(m2m_bundle, m2m_resource))
        
        return m2m_dehydrated
    
    def hydrate(self, bundle):
        pass
    
    def hydrate_m2m(self, bundle):
        if bundle.data.get(self.instance_name) is None:
            if self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a null value." % self.instance_name)
        
        m2m_hydrated = []
        
        for value in bundle.data.get(self.instance_name):
            m2m_hydrated.append(self.build_related_resource(value))
        
        return m2m_hydrated


class ManyToManyField(ToManyField):
    pass


class OneToManyField(ToManyField):
    pass


# DRL_FIXME: Need more types?
#
#   + AutoField
#   + BooleanField
#   + CharField
#   - CommaSeparatedIntegerField
#   + DateField
#   + DateTimeField
#   - DecimalField
#   - EmailField
#   - FileField
#   - FilePathField
#   + FloatField
#   - ImageField
#   + IntegerField
#   - IPAddressField
#   + NullBooleanField
#   + PositiveIntegerField
#   + PositiveSmallIntegerField
#   - SlugField
#   + SmallIntegerField
#   - TextField
#   - TimeField
#   - URLField
#   - XMLField
#   + ForeignKey
#   + ManyToManyField
#   - OneToOneField


