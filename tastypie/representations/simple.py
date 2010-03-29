from tastypie.fields import ApiField


class DeclarativeMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['fields'] = {}
        
        # Inherit any fields from parent(s).
        try:
            parents = [b for b in bases if issubclass(b, Representation)]
            
            for p in parents:
                fields = getattr(p, 'fields', None)
                
                if fields:
                    attrs['fields'].update(fields)
        except NameError:
            pass
        
        for field_name, obj in attrs.items():
            if isinstance(obj, ApiField):
                field = attrs.pop(field_name)
                field.set_instance_name(field_name)
                attrs['fields'][field_name] = field
        
        return super(DeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)


class Representation(object):
    """
    By default, handles the CRUD operations for a single object.
    
    Should be pure data (fields + data object).
    """
    __metaclass__ = DeclarativeMetaclass
    
    @classmethod
    def get_list(cls, **kwargs):
        raise NotImplementedError
    
    def get(self, **kwargs):
        raise NotImplementedError
    
    def create(self, data_dict):
        raise NotImplementedError
    
    def update(self, **kwargs):
        raise NotImplementedError
    
    def delete(self):
        raise NotImplementedError
    
    def get_resource_uri(self):
        """
        This needs to be implemented at the user level.
        
        A ``return reverse("api_%s_detail" % object_name, kwargs={'obj_id': object.id})``
        should be all that would be needed.
        """
        raise NotImplementedError
    
    def full_dehydrate(self, obj):
        dehydrated_object = {}
        
        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            dehydrated_object[field_name] = field_object.dehydrate()
        
        # Run through optional overrides.
        for field_name in self.fields:
            method = getattr(self, "dehydrate_%s" % field_name, None)
            
            if method:
                dehydrated_object[field_name] = method()
        
        dehydrated_object.update(self.dehydrate())
        return dehydrated_object
    
    def dehydrate(self, obj):
        return {}
    
    def full_hydrate(self, data):
        self.hydrate(data)
        
        for key, value in data.items():
            if key in self.fields:
                self.fields[key] = value
        
        for key, value in data.items():
            method = getattr(self, "hydrate_%s" % key, None)
            
            if method:
                self.fields[key] = method(data)
    
    def hydrate(self, data):
        return None
    