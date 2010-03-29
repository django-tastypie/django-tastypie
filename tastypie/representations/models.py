from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
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
        super(ModelRepresentation, self).__init__(*args, **kwargs)
        
        # Introspect the model, adding/removing fields as needed.
        # Adds/Excludes should happen only if the fields are not already
        # defined in `self.fields`.
        self._meta = getattr(self, 'Meta', None)
        
        if self._meta:
            self.queryset = getattr(self._meta, 'queryset', None)
            
            if self.queryset is None:
                raise ImproperlyConfigured("Using the ModelRepresentation requires providing a model.")
            
            self.model = self.queryset.model
            fields = getattr(self._meta, 'fields', [])
            excludes = getattr(self._meta, 'excludes', [])
            
            # Add in the new fields.
            self.fields.update(self.get_fields(fields, excludes))
    
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
        
        for f in self.model._meta.fields:
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
            
            kwargs.update({
                'attribute': f.name,
            })
            
            if f.null is True:
                kwargs['null'] = True
            
            if f.has_default():
                kwargs['default'] = f.default
            
            final_fields[f.name] = api_field_class(**kwargs)
            final_fields[f.name].instance_name = f.name
        
        return final_fields
    
    @classmethod
    def get_list(cls, **kwargs):
        model_list = cls.queryset.filter(**kwargs)
        representations = []
        
        for model in model_list:
            represent = cls()
            represent.full_dehydrate(model)
            representations.append(represent)
        
        return representations
    
    def get(self, **kwargs):
        try:
            model = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.full_dehydrate(model)
    
    def create(self, data_dict):
        self.full_hydrate(data_dict)
        newbie = self.model()
        
        for field_name, field_object in self.fields:
            setattr(newbie, field_object.attribute, field_object.data)
        
        newbie.save()
    
    def update(self, **kwargs):
        try:
            model = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.full_hydrate(data_dict)
        
        for field_name, field_object in self.fields:
            setattr(model, field_object.attribute, field_object.data)
        
        model.save()
    
    def delete(self):
        try:
            model = self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        
        model.delete()
    