import re
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.utils import datetime_safe
from tastypie.exceptions import ApiFieldError


class NOT_PROVIDED:
    pass


DATE_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).*?$')
DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).*?$')


# All the ApiField variants.

class ApiField(object):
    dehydrated_type = 'string'
    
    """The base implementation of a field used by the representations."""
    def __init__(self, attribute=None, default=NOT_PROVIDED, null=False, readonly=False):
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
    
    def dehydrate(self, obj):
        """
        Takes data from the provided object and prepares it for the
        representation.
        """
        if self.attribute is not None:
            # Check for `__` in the field for looking through the relation.
            attrs = self.attribute.split('__')
            current_object = obj
            
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
                        raise ApiFieldError("The model '%s' has an empty attribute '%s' and doesn't allow a default or null value." % (repr(current_object), attr))
            
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
    
    def hydrate(self):
        if self.readonly:
            return None
        
        if self.value is None:
            if self.has_default():
                if callable(self._default):
                    return self._default()
                
                return self._default
            elif self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a default or null value." % self.instance_name)
        
        return self.value


class CharField(ApiField):
    dehydrated_type = 'string'
    
    def dehydrate(self, obj):
        return self.convert(super(CharField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return unicode(value)


class IntegerField(ApiField):
    dehydrated_type = 'integer'
    
    def dehydrate(self, obj):
        return self.convert(super(IntegerField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return int(value)


class FloatField(ApiField):
    dehydrated_type = 'float'
    
    def dehydrate(self, obj):
        return self.convert(super(FloatField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return float(value)


class BooleanField(ApiField):
    dehydrated_type = 'boolean'
    
    def dehydrate(self, obj):
        return self.convert(super(BooleanField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return bool(value)


class DateField(ApiField):
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


class DateTimeField(ApiField):
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


class RelatedField(ApiField):
    dehydrated_type = 'related'
    is_related = True
    
    # TODO: This is leaky when dealing with non-model representations.
    #       Without a good use case, there's not a good way to solve this
    #       for now.
    def __init__(self, to, attribute, related_name=None, null=False, full_repr=False):
        self.instance_name = None
        self.to = to
        self.attribute = attribute
        self.related_name = related_name
        self.null = null
        self.full_repr = full_repr
        self.value = None
        self.api_name = None
        self.resource_name = None
    
    def has_default(self):
        return False
    
    @property
    def default(self):
        raise ApiFieldError("%r fields do not have default data." % repr(self))
    
    def get_related_representation(self, related_instance):
        # TODO: More leakage.
        related_repr = self.to(api_name=self.api_name, resource_name=self.resource_name)
        # Try to be efficient about DB queries.
        related_repr.instance = related_instance
        return related_repr
    
    def dehydrate_related(self, related_repr):
        if not self.full_repr:
            # Be a good netizen.
            return related_repr.get_resource_uri()
        else:
            # ZOMG extra data and big payloads.
            related_repr.full_dehydrate(related_repr.instance)
            return related_repr
    
    def build_related_representation(self, value):
        if isinstance(value, basestring):
            # We got a URI. Load the object and assign it.
            self.fk_repr = self.to()
            
            try:
                self.fk_repr.get_via_uri(value)
                return self.fk_repr
            except ObjectDoesNotExist:
                raise ApiFieldError("Could not find the provided object via resource URI '%s'." % value)
        elif hasattr(value, 'items'):
            # Try to hydrate the data provided.
            # TODO: This assumes a dictionary-like structure. I think that's
            #       fine but we may wish to re-evaluate that.
            self.fk_repr = self.to(data=value)
            return self.fk_repr
        else:
            raise ApiFieldError("The '%s' field has was given data that was not a URI and not a dictionary-alike: %s." % (self.instance_name, value))


class ForeignKey(RelatedField):
    def __init__(self, to, attribute, related_name=None, null=False, full_repr=False):
        super(ForeignKey, self).__init__(to, attribute, related_name, null=null, full_repr=full_repr)
        self.fk_repr = None
    
    def dehydrate(self, obj):
        if not getattr(obj, self.attribute):
            if not self.null:
                raise ApiFieldError("The model '%s' has an empty attribute '%s' and doesn't allow a null value." % (repr(obj), self.attribute))
            
            return None
        
        self.fk_repr = self.get_related_representation(getattr(obj, self.attribute))
        return self.dehydrate_related(self.fk_repr)
    
    def hydrate(self):
        if self.value is None:
            if self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a null value." % self.instance_name)
        
        return self.build_related_representation(self.value)


class ManyToManyField(RelatedField):
    is_m2m = True
    
    def __init__(self, to, attribute, related_name=None, null=False, full_repr=False):
        super(ManyToManyField, self).__init__(to, attribute, related_name, null=null, full_repr=full_repr)
        self.m2m_reprs = []
    
    def dehydrate(self, obj):
        if not obj.pk:
            if not self.null:
                raise ApiFieldError("The model '%s' does not have a primary key and can not be used in a ManyToMany context." % repr(obj))
            
            return []
        
        if not getattr(obj, self.attribute):
            if not self.null:
                raise ApiFieldError("The model '%s' has an empty attribute '%s' and doesn't allow a null value." % (repr(obj), self.attribute))
            
            return []
        
        self.m2m_reprs = []
        m2m_dehydrated = []
        
        # TODO: Also model-specific and leaky. Relies on there being a
        #       ``Manager`` there.
        for m2m in getattr(obj, self.attribute).all():
            m2m_repr = self.get_related_representation(m2m)
            self.m2m_reprs.append(m2m_repr)
            m2m_dehydrated.append(self.dehydrate_related(m2m_repr))
        
        return m2m_dehydrated
    
    def hydrate(self):
        pass
    
    def hydrate_m2m(self):
        if self.value is None:
            if self.null:
                return None
            else:
                raise ApiFieldError("The '%s' field has no data and doesn't allow a null value." % self.instance_name)
        
        m2m_hydrated = []
        
        for value in self.value:
            m2m_hydrated.append(self.build_related_representation(value))
        
        return m2m_hydrated


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


