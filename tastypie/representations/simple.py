from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch
from django.utils.copycompat import deepcopy, copy
from tastypie.exceptions import HydrationError
from tastypie.fields import ApiField, CharField, RelatedField


class DeclarativeMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = {}
        
        # Inherit any fields from parent(s).
        try:
            parents = [b for b in bases if issubclass(b, Representation)]
            
            for p in parents:
                fields = getattr(p, 'base_fields', None)
                
                if fields:
                    attrs['base_fields'].update(fields)
        except NameError:
            pass
        
        for field_name, obj in attrs.items():
            if isinstance(obj, ApiField):
                field = attrs.pop(field_name)
                field.instance_name = field_name
                attrs['base_fields'][field_name] = field
        
        new_class = super(DeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)
        new_class._meta = getattr(new_class, 'Meta', None)
        
        if not new_class._meta:
            raise ImproperlyConfigured("An inner Meta class is required to configure '%r'." % new_class)
        
        return new_class


class Representation(object):
    """
    By default, handles the CRUD operations for a single object.
    
    Should be pure data (fields + data object).
    """
    __metaclass__ = DeclarativeMetaclass
    
    def __init__(self, api_name=None, resource_name=None, data={}):
        self.object_class = getattr(self._meta, 'object_class', None)
        self.instance = None
        self.api_name = api_name or ''
        self.resource_name = resource_name or ''
        
        # Use a copy of the field instances, not the ones actually stored on
        # the class.
        self.fields = deepcopy(self.base_fields)
        
        if getattr(self._meta, 'include_resource_uri', True) and not 'resource_uri' in self.fields:
            self.fields['resource_uri'] = CharField(readonly=True)
        
        # Now that we have fields, populate fields via kwargs if found.
        for key, value in data.items():
            if key in self.fields:
                self.fields[key].value = value
        
        if self.object_class is None:
            raise ImproperlyConfigured("Using the Representation requires providing an object_class in the inner Meta class.")
    
    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
    
    @classmethod
    def get_list(cls, **kwargs):
        raise NotImplementedError()
    
    @classmethod
    def delete_list(cls, **kwargs):
        raise NotImplementedError()
    
    def get(self, **kwargs):
        raise NotImplementedError()
    
    def create(self):
        raise NotImplementedError()
    
    def update(self, **kwargs):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()
    
    def get_resource_uri(self):
        """
        This needs to be implemented at the user level.
        
        A ``return reverse("api_dispatch_detail", kwargs={'resource_name':
        self.resource_name, 'obj_id': object.id})`` should be all that would
        be needed.
        """
        raise NotImplementedError()
    
    def get_via_uri(self, uri):
        """
        This needs to be implemented at the user level.
        
        This pulls apart the salient bits of the URI and populates the
        representation via a ``get`` with the ``obj_id``.
        
        Example::
        
            def get_via_uri(self, uri):
                view, args, kwargs = resolve(uri)
                return self.get(obj_id=kwargs['obj_id'])
        
        If you need custom behavior based on other portions of the URI,
        simply override this method.
        """
        raise NotImplementedError()
    
    def full_dehydrate(self, obj):
        """
        Given an object instance, extract the information from it to populate
        the representation.
        """
        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            # A touch leaky but it makes URI resolution work.
            if isinstance(field_object, RelatedField):
                field_object.api_name = self.api_name
                field_object.resource_name = self.resource_name
                
            field_object.value = field_object.dehydrate(obj)
        
        # Run through optional overrides.
        for field_name, field_object in self.fields.items():
            method = getattr(self, "dehydrate_%s" % field_name, None)
            
            if method:
                field_object.value = method(obj)
        
        self.dehydrate(obj)
    
    def dehydrate(self, obj):
        pass
    
    def full_hydrate(self):
        """
        Given a populated representation, distill it and turn it back into
        a full-fledged object instance.
        """
        if self.instance is None:
            self.instance = self.object_class()
        
        for field_name, field_object in self.fields.items():
            if field_object.attribute:
                value = field_object.hydrate()
                
                if value is not None:
                    # We need to avoid populating M2M data here as that will
                    # cause things to blow up.
                    if not getattr(field_object, 'is_related', False):
                        setattr(self.instance, field_object.attribute, value)
                    elif not getattr(field_object, 'is_m2m', False):
                        setattr(self.instance, field_object.attribute, value.instance)
        
        for field_name, field_object in self.fields.items():
            method = getattr(self, "hydrate_%s" % field_name, None)
            
            if method:
                method()
        
        self.hydrate()
    
    def hydrate(self):
        pass
    
    def hydrate_m2m(self):
        """
        Populate the ManyToMany data on the instance.
        """
        if self.instance is None:
            raise HydrationError("You must call 'full_hydrate' before attempting to run 'hydrate_m2m' on %r." % self)
        
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            if field_object.attribute:
                # Note that we only hydrate the data, leaving the instance
                # unmodified. It's up to the user's code to handle this.
                # The ``ModelRepresentation`` provides a working baseline
                # in this regard.
                field_object.value = field_object.hydrate_m2m()
        
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue
            
            method = getattr(self, "hydrate_%s" % field_name, None)
            
            if method:
                method()
    
    def to_dict(self):
        data = {}
        
        for field_name, field_object in self.fields.items():
            data[field_name] = field_object.value
        
        return data
    
    def build_schema(self):
        data = {}
        
        for field_name, field_object in self.fields.items():
            data[field_name] = {
                'type': field_object.dehydrated_type,
                'nullable': field_object.null,
                'readonly': field_object.readonly,
            }
        
        return data
    
    def dehydrate_resource_uri(self, obj):
        try:
            return self.get_resource_uri()
        except NotImplementedError:
            return ''
        except NoReverseMatch:
            return ''
    
    class Meta:
        pass

class RepresentationSet(object):
    """
    Lazy representation iterable, used for operating on representations using slices.
    """
    def __init__(self, representation_class, data, options):
        self.representation_class = representation_class
        self.data = data
        self.options = options
        self.slice = slice(None)

    def __getitem__(self, key):
        if isinstance(key, slice):
            new_set = copy(self)
            new_set.slice = key
            return new_set
        else:
            return self.build_representation(self.data[key])

    def __iter__(self):
        for instance in self.data[self.slice]:
            representation = self.build_representation(instance)
            yield representation

    def __len__(self):
        return len(self.data[self.slice])

    def build_representation(self, instance):
        representation = self.representation_class(**self.options)
        representation.instance = instance
        representation.full_dehydrate(instance)
        return representation
