from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.copycompat import deepcopy
from tastypie.exceptions import NotFound
from tastypie.fields import *
from tastypie.representations.simple import Representation


def api_field_from_django_field(f, default=CharField):
    """
    Returns the field type that would likely be associated with each
    Django type.
    """
    result = default
    
    if f.get_internal_type() in ('DateField', 'DateTimeField'):
        result = DateTimeField
    elif f.get_internal_type() in ('BooleanField', 'NullBooleanField'):
        result = BooleanField
    elif f.get_internal_type() in ('DecimalField', 'FloatField'):
        result = FloatField
    elif f.get_internal_type() in ('IntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 'SmallIntegerField'):
        result = IntegerField
    
    return result


class ModelRepresentation(Representation):
    """
    Acts like a normal Representation but implements all of Django's ORM calls.
    
    Example::
    
        class NoteRepr(ModelRepresentation):
            class Meta:
                queryset = Note
                fields = ['title', 'author', 'content', 'pub_date']
            
            def dehydrate_author(self, model):
                return model.user.username
            
            def hydrate_author(self, obj):
                return User.objects.get_or_create(username=obj.author)
    """
    def __init__(self, *args, **kwargs):
        self._meta = getattr(self, 'Meta', None)
        
        if not self._meta:
            raise ImproperlyConfigured("An inner Meta class is required to configure %s." % repr(self))
        
        # Introspect the model, adding/removing fields as needed.
        # Adds/Excludes should happen only if the fields are not already
        # defined in `self.fields`.
        self.queryset = getattr(self._meta, 'queryset', None)
        self.instance = None
        
        if self.queryset is None:
            raise ImproperlyConfigured("Using the ModelRepresentation requires providing a model.")
        
        self.object_class = self.queryset.model
        self.fields = deepcopy(self.base_fields)
        fields = getattr(self._meta, 'fields', [])
        excludes = getattr(self._meta, 'excludes', [])
        
        # Add in the new fields.
        self.fields.update(self.get_fields(fields, excludes))
        
        # Now that we have fields, populate fields via kwargs if found.
        # TODO: Unrecognized fields get silently ignored and throw away.
        #       Seems like this could go either way on behavior.
        for key, value in kwargs.items():
            if key in self.fields:
                self.fields[key].value = value
        
        if self.object_class is None:
            raise ImproperlyConfigured("Using the Representation requires providing an object_class in the inner Meta class.")
    
    def should_skip_field(self, field):
        """
        Given a Django model field, return if it should be included in the
        contributed ApiFields.
        """
        # Ignore certain fields (AutoField, related fields).
        if field.primary_key or getattr(field, 'rel'):
            return True
        
        return False
    
    def get_fields(self, fields=None, excludes=None):
        """
        Given any explicit fields to include and fields to exclude, add
        additional fields based on the associated model.
        """
        final_fields = {}
        fields = fields or []
        excludes = excludes or []
        
        for f in self.object_class._meta.fields:
            # If the field name is already present, skip
            if f.name in self.fields:
                continue
            
            # If field is not present in explicit field listing, skip
            if fields and f.name not in fields:
                continue
            
            # If field is in exclude list, skip
            if excludes and f.name in excludes:
                continue
            
            if self.should_skip_field(f):
                continue
            
            api_field_class = api_field_from_django_field(f)
            
            kwargs = {
                'attribute': f.name,
            }
            
            if f.null is True:
                kwargs['null'] = True
            
            if f.has_default():
                kwargs['default'] = f.default
            
            final_fields[f.name] = api_field_class(**kwargs)
            final_fields[f.name].instance_name = f.name
        
        return final_fields
    
    # FIXME: This ought to be a classmethod, but assigning the queryset to the
    #        class is problematic given the existing code.
    # @classmethod
    def get_list(self, **kwargs):
        model_list = self.queryset.filter(**kwargs)
        representations = []
        
        for model in model_list:
            represent = self.__class__()
            represent.full_dehydrate(model)
            representations.append(represent)
        
        return representations
    
    def get(self, **kwargs):
        try:
            self.instance = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.full_dehydrate(self.instance)
    
    def create(self, **kwargs):
        self.instance = self.object_class()
        
        for key, value in kwargs.items():
            setattr(self.instance, key, value)
        
        self.full_hydrate()
        self.instance.save()
    
    def update(self, **kwargs):
        try:
            self.instance = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.full_hydrate()
        self.instance.save()
    
    def delete(self, **kwargs):
        try:
            self.instance = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.instance.delete()
    