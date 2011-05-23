from dateutil.parser import parse
from decimal import Decimal
import re
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import datetime_safe, importlib
from tastypie.bundle import Bundle
from tastypie.exceptions import ApiFieldError, NotFound
from tastypie.utils import dict_strip_unicode_keys


class NOT_PROVIDED:
    pass


DATE_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).*?$')
DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).*?$')


# All the ApiField variants.

class ApiField(object):
    """The base implementation of a field used by the resources."""
    dehydrated_type = 'string'
    help_text = ''
    
    def __init__(self, attribute=None, default=NOT_PROVIDED, null=False, readonly=False, unique=False, help_text=None):
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
        
        Optionally accepts a ``unique``, which indicates if the field is a
        unique identifier for the object.
        
        Optionally accepts ``help_text``, which lets you provide a
        human-readable description of the field exposed at the schema level.
        Defaults to the per-Field definition.
        """
        # Track what the index thinks this field is called.
        self.instance_name = None
        self._resource = None
        self.attribute = attribute
        self._default = default
        self.null = null
        self.readonly = readonly
        self.value = None
        self.unique = unique
        
        if help_text:
            self.help_text = help_text
    
    def contribute_to_class(self, cls, name):
        # Do the least we can here so that we don't hate ourselves in the
        # morning.
        self.instance_name = name
        self._resource = cls
    
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
                previous_object = current_object
                current_object = getattr(current_object, attr, None)
                
                if current_object is None:
                    if self.has_default():
                        current_object = self._default
                        # Fall out of the loop, given any further attempts at
                        # accesses will fail miserably.
                        break
                    elif self.null:
                        current_object = None
                        # Fall out of the loop, given any further attempts at
                        # accesses will fail miserably.
                        break
                    else:
                        raise ApiFieldError("The object '%r' has an empty attribute '%s' and doesn't allow a default or null value." % (previous_object, attr))
            
            if callable(current_object):
                current_object = current_object()
            
            return self.convert(current_object)
        
        if self.has_default():
            return self.convert(self.default)
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
        
        if not bundle.data.has_key(self.instance_name):
            if self.attribute and getattr(bundle.obj, self.attribute, None):
                return getattr(bundle.obj, self.attribute)
            elif self.instance_name and hasattr(bundle.obj, self.instance_name):
                return getattr(bundle.obj, self.instance_name)
            elif self.has_default():
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
    help_text = 'Unicode string data. Ex: "Hello World"'
    
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
    help_text = 'A file URL as a string. Ex: "http://media.example.com/media/photos/my_photo.jpg"'
    
    def convert(self, value):
        if value is None:
            return None
        
        try:
            # Try to return the URL if it's a ``File``, falling back to the string
            # itself if it's been overridden or is a default.
            return getattr(value, 'url', value)
        except ValueError:
            return None


class IntegerField(ApiField):
    """
    An integer field.
    
    Covers ``models.IntegerField``, ``models.PositiveIntegerField``,
    ``models.PositiveSmallIntegerField`` and ``models.SmallIntegerField``.
    """
    dehydrated_type = 'integer'
    help_text = 'Integer data. Ex: 2673'
    
    def convert(self, value):
        if value is None:
            return None
        
        return int(value)


class FloatField(ApiField):
    """
    A floating point field.
    """
    dehydrated_type = 'float'
    help_text = 'Floating point numeric data. Ex: 26.73'
    
    def convert(self, value):
        if value is None:
            return None
        
        return float(value)


class DecimalField(ApiField):
    """
    A decimal field.
    """
    dehydrated_type = 'decimal'
    help_text = 'Fixed precision numeric data. Ex: 26.73'
    
    def convert(self, value):
        if value is None:
            return None
        
        return Decimal(value)


class BooleanField(ApiField):
    """
    A boolean field.
    
    Covers both ``models.BooleanField`` and ``models.NullBooleanField``.
    """
    dehydrated_type = 'boolean'
    help_text = 'Boolean data. Ex: True'
    
    def convert(self, value):
        if value is None:
            return None
        
        return bool(value)


class ListField(ApiField):
    """
    A list field.
    """
    dehydrated_type = 'list'
    help_text = "A list of data. Ex: ['abc', 26.73, 8]"
    
    def convert(self, value):
        if value is None:
            return None
        
        return list(value)


class DictField(ApiField):
    """
    A dictionary field.
    """
    dehydrated_type = 'dict'
    help_text = "A dictionary of data. Ex: {'price': 26.73, 'name': 'Daniel'}"
    
    def convert(self, value):
        if value is None:
            return None
        
        return dict(value)


class DateField(ApiField):
    """
    A date field.
    """
    dehydrated_type = 'date'
    help_text = 'A date as a string. Ex: "2010-11-10"'
    
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
    help_text = 'A date & time as a string. Ex: "2010-11-10T03:07:43"'
    
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
    
    The ``RelatedField`` base class is not intended for direct use but provides
    functionality that ``ToOneField`` and ``ToManyField`` build upon.
    
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
    help_text = 'A related resource. Can be either a URI or set of nested resource data.'
    
    def __init__(self, to, attribute, related_name=None, default=NOT_PROVIDED, null=False, full=False, unique=False, help_text=None):
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
        self._resource = None
        self.to = to
        self.attribute = attribute
        self.related_name = related_name
        self._default = default
        self.null = null
        self.full = full
        self.readonly = False
        self.api_name = None
        self.resource_name = None
        self.unique = unique
        self._to_class = None
        
        if self.to == 'self':
            self.self_referential = True
            self._to_class = self.__class__
        
        if help_text:
            self.help_text = help_text
    
    def contribute_to_class(self, cls, name):
        super(RelatedField, self).contribute_to_class(cls, name)
        
        # Check if we're self-referential and hook it up.
        # We can't do this quite like Django because there's no ``AppCache``
        # here (which I think we should avoid as long as possible).
        if self.self_referential or self.to == 'self':
            self._to_class = cls
    
    def get_related_resource(self, related_instance):
        """
        Instaniates the related resource.
        """
        related_resource = self.to_class()
        
        # Fix the ``api_name`` if it's not present.
        if related_resource._meta.api_name is None:
            if self._resource and not self._resource._meta.api_name is None:
                related_resource._meta.api_name = self._resource._meta.api_name
        
        # Try to be efficient about DB queries.
        related_resource.instance = related_instance
        return related_resource
    
    @property
    def to_class(self):
        # We need to be lazy here, because when the metaclass constructs the
        # Resources, other classes may not exist yet.
        # That said, memoize this so we never have to relookup/reimport.
        if self._to_class:
            return self._to_class
        
        if not isinstance(self.to, basestring):
            self._to_class = self.to
            return self._to_class
        
        # It's a string. Let's figure it out.
        if '.' in self.to:
            # Try to import.
            module_bits = self.to.split('.')
            module_path, class_name = '.'.join(module_bits[:-1]), module_bits[-1]
            module = importlib.import_module(module_path)
        else:
            # We've got a bare class name here, which won't work (No AppCache
            # to rely on). Try to throw a useful error.
            raise ImportError("Tastypie requires a Python-style path (<module.module.Class>) to lazy load related resources. Only given '%s'." % self.to)
        
        self._to_class = getattr(module, class_name, None)
        
        if self._to_class is None:
            raise ImportError("Module '%s' does not appear to have a class called '%s'." % (module_path, class_name))
        
        return self._to_class
    
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
        self.fk_resource = self.to_class()
        
        if isinstance(value, basestring):
            # We got a URI. Load the object and assign it.
            try:
                obj = self.fk_resource.get_via_uri(value)
                return self.fk_resource.full_dehydrate(obj)
            except ObjectDoesNotExist:
                raise ApiFieldError("Could not find the provided object via resource URI '%s'." % value)
        elif hasattr(value, 'items'):
            # Try to hydrate the data provided.
            value = dict_strip_unicode_keys(value)
            self.fk_bundle = Bundle(data=value)
            
            # We need to check to see if updates are allowed on the FK
            # resource. If not, we'll just return a populated bundle instead
            # of mistakenly updating something that should be read-only.
            if not self.fk_resource.can_update():
                return self.fk_resource.full_hydrate(self.fk_bundle)
            
            try:
                return self.fk_resource.obj_update(self.fk_bundle, **value)
            except NotFound:
                try:
                    # Attempt lookup by primary key
                    lookup_kwargs = dict((k, v) for k, v in value.iteritems() if getattr(self.fk_resource, k).unique)
                    
                    if not lookup_kwargs:
                        raise NotFound()
                    
                    return self.fk_resource.obj_update(self.fk_bundle, **lookup_kwargs)
                except NotFound:
                    return self.fk_resource.full_hydrate(self.fk_bundle)
            except MultipleObjectsReturned:
                return self.fk_resource.full_hydrate(self.fk_bundle)
        elif hasattr(value, 'pk'):
            return self.fk_resource.full_dehydrate(value)
        else:
            raise ApiFieldError("The '%s' field has was given data that was not a URI and not a dictionary-alike: %s." % (self.instance_name, value))


class ToOneField(RelatedField):
    """
    Provides access to related data via foreign key.
    
    This subclass requires Django's ORM layer to work properly.
    """
    help_text = 'A single related resource. Can be either a URI or set of nested resource data.'
    
    def __init__(self, to, attribute, related_name=None, default=NOT_PROVIDED, null=False, full=False, unique=False, help_text=None):
        super(ToOneField, self).__init__(to, attribute, related_name=related_name, default=default, null=null, full=full, unique=unique, help_text=help_text)
        self.fk_resource = None
    
    def dehydrate(self, bundle):
        try:
            foreign_obj = getattr(bundle.obj, self.attribute)
        except ObjectDoesNotExist:
            foreign_obj = None
        
        if not foreign_obj:
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (bundle.obj, self.attribute))
            
            return None
        
        self.fk_resource = self.get_related_resource(foreign_obj)
        fk_bundle = Bundle(obj=foreign_obj)
        return self.dehydrate_related(fk_bundle, self.fk_resource)
    
    def hydrate(self, bundle):
        value = super(ToOneField, self).hydrate(bundle)
        
        if value is None:
            return value
        
        return self.build_related_resource(value)

class ForeignKey(ToOneField):
    """
    A convenience subclass for those who prefer to mirror ``django.db.models``.
    """
    pass


class OneToOneField(ToOneField):
    """
    A convenience subclass for those who prefer to mirror ``django.db.models``.
    """
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
    help_text = 'Many related resources. Can be either a list of URIs or list of individually nested resource data.'
    
    def __init__(self, to, attribute, related_name=None, default=NOT_PROVIDED, null=False, full=False, unique=False, help_text=None):
        super(ToManyField, self).__init__(to, attribute, related_name=related_name, default=default, null=null, full=full, unique=unique, help_text=help_text)
        self.m2m_bundles = []
    
    def dehydrate(self, bundle):
        if not bundle.obj or not bundle.obj.pk:
            if not self.null:
                raise ApiFieldError("The model '%r' does not have a primary key and can not be used in a ToMany context." % bundle.obj)
            
            return []
        
        if isinstance(self.attribute, basestring):
            the_m2ms = getattr(bundle.obj, self.attribute)
        elif callable(self.attribute):
            the_m2ms = self.attribute(bundle)
        
        if not the_m2ms:
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (bundle.obj, self.attribute))
            
            return []
        
        self.m2m_resources = []
        m2m_dehydrated = []
        
        # TODO: Also model-specific and leaky. Relies on there being a
        #       ``Manager`` there.
        for m2m in the_m2ms.all():
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
                return []
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a null value." % self.instance_name)
        
        m2m_hydrated = []
        
        for value in bundle.data.get(self.instance_name):
            if value is None:
                continue
            
            m2m_hydrated.append(self.build_related_resource(value))
        
        return m2m_hydrated


class ManyToManyField(ToManyField):
    """
    A convenience subclass for those who prefer to mirror ``django.db.models``.
    """
    pass


class OneToManyField(ToManyField):
    """
    A convenience subclass for those who prefer to mirror ``django.db.models``.
    """
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
#   + FileField
#   + FilePathField
#   + FloatField
#   + ImageField
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
#   + OneToOneField


