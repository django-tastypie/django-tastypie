import re
from django.utils import datetime_safe
from tastypie.exceptions import ApiFieldError


class NOT_PROVIDED:
    pass


DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).*?$')


# All the ApiField variants.

class ApiField(object):
    """The base implementation of a field used by the representations."""
    def __init__(self, attribute=None, default=NOT_PROVIDED, null=False):
        # Track what the index thinks this field is called.
        self.instance_name = None
        self.attribute = attribute
        self._default = default
        self.null = null
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
    def dehydrate(self, obj):
        return self.convert(super(CharField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return unicode(value)


class IntegerField(ApiField):
    def dehydrate(self, obj):
        return self.convert(super(IntegerField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return int(value)


class FloatField(ApiField):
    def dehydrate(self, obj):
        return self.convert(super(FloatField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return float(value)


class BooleanField(ApiField):
    def dehydrate(self, obj):
        return self.convert(super(BooleanField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return bool(value)


class DateField(ApiField):
    def convert(self, value):
        if value is None:
            return None
        
        if isinstance(value, basestring):
            match = DATETIME_REGEX.search(value)
            
            if match:
                data = match.groupdict()
                return datetime_safe.date(int(data['year']), int(data['month']), int(data['day']))
            else:
                raise ApiFieldError("Date provided to '%s' field doesn't appear to be a valid date string: '%s'" % (self.instance_name, value))
        
        return value


class DateTimeField(ApiField):
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


# DRL_FIXME: Need more types.
