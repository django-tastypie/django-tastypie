from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve, NoReverseMatch, Resolver404
from django.utils.copycompat import deepcopy
from tastypie import _get_canonical_resource_name
from tastypie.exceptions import NotFound, URLReverseError
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
    # TODO: Enable these via introspection. The reason they're not enabled
    #       by default is the very different ``__init__`` they have over
    #       the other fields.
    # elif f.get_internal_type() == 'ForeignKey':
    #     result = ForeignKey
    # elif f.get_internal_type() == 'ManyToManyField':
    #     result = ManyToManyField
    
    return result


class ModelRepresentation(Representation):
    """
    Acts like a normal Representation but implements all of Django's ORM calls.
    
    Example::
    
        class NoteRepr(ModelRepresentation):
            class Meta:
                queryset = Note
                fields = ['title', 'author', 'content', 'pub_date']
            
            def dehydrate_author(self, obj):
                return obj.user.username
            
            def hydrate_author(self):
                self.instance.author = User.objects.get_or_create(username=self.author.value)
    """
    def __init__(self, api_name=None, resource_name=None, data={}):
        self.queryset = getattr(self._meta, 'queryset', None)
        self.api_name = api_name or ''
        self.resource_name = resource_name or ''
        
        # Introspect the model, adding/removing fields as needed.
        # Adds/Excludes should happen only if the fields are not already
        # defined in `self.fields`.
        self.instance = None
        
        if self.queryset is None:
            raise ImproperlyConfigured("Using the ModelRepresentation requires providing a model.")
        
        self.object_class = self.queryset.model
        self.fields = deepcopy(self.base_fields)
        
        if getattr(self._meta, 'include_resource_uri', True) and not 'resource_uri' in self.fields:
            self.fields['resource_uri'] = CharField(readonly=True)
        
        fields = getattr(self._meta, 'fields', [])
        excludes = getattr(self._meta, 'excludes', [])
        
        # Add in the new fields.
        self.fields.update(self.get_fields(fields, excludes))
        
        # Now that we have fields, populate fields via kwargs if found.
        for key, value in data.items():
            if key in self.fields:
                self.fields[key].value = value
        
        if self.object_class is None:
            raise ImproperlyConfigured("Using the Representation requires providing an object_class in the inner Meta class.")
    
    # FIXME: Once relations are supported, this needs to be modified to allow
    #        them through.
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
            
            # FIXME: There's a potential edge-case here dealing with ``blank-True``.
            # if f.blank is True:
            #     kwargs['default'] = ''
            
            if f.has_default():
                kwargs['default'] = f.default
            
            final_fields[f.name] = api_field_class(**kwargs)
            final_fields[f.name].instance_name = f.name
        
        return final_fields
    
    @classmethod
    def get_list(cls, options=None, **kwargs):
        options = options or {}
        model_list = cls._meta.queryset.filter(**kwargs)
        representations = []
        
        for model in model_list:
            represent = cls(**options)
            represent.instance = model
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
        
        # Now pick up the M2M bits.
        self.hydrate_m2m()
        self.save_m2m()
    
    def update(self, **kwargs):
        if self.instance is None:
            try:
                self.instance = self.queryset.get(**kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.full_hydrate()
        self.instance.save()
        
        # Now pick up the M2M bits.
        self.hydrate_m2m()
        self.save_m2m()
    
    def delete(self, **kwargs):
        if self.instance is None:
            try:
                self.instance = self.queryset.get(**kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")
        
        self.instance.delete()
    
    def save_m2m(self):
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            if not field_object.attribute:
                continue
            
            # Get the manager.
            related_mngr = getattr(self.instance, field_object.attribute)
            
            if hasattr(related_mngr, 'clear'):
                # Clear it out, just to be safe.
                related_mngr.clear()
            
            related_mngr.add(*[related_repr.instance for related_repr in field_object.value])
    
    def get_resource_uri(self):
        kwargs = {
            'resource_name': self.resource_name,
            'obj_id': self.instance.id
        }
        
        if self.api_name is not None:
            try:
                kwargs['resource_name'] =  _get_canonical_resource_name(self.api_name, self)
            except URLReverseError:
                pass
            
            kwargs['api_name'] = self.api_name
        
        return reverse("api_dispatch_detail", kwargs=kwargs)
    
    def get_via_uri(self, uri):
        try:
            view, args, kwargs = resolve(uri)
        except Resolver404:
            raise NotFound("The URL provided '%s' was not a link to a valid resource." % uri)
        
        return self.get(id=kwargs['obj_id'])
