try:
    from django.conf.urls import patterns, include
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, include
from tastypie import fields
from tastypie.resources import ModelResource
from core.models import Note, Subject
from core.tests.api import Api, UserResource


class SubjectResource(ModelResource):
    class Meta:
        resource_name = 'subjects'
        queryset = Subject.objects.all()


class CustomNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    subjects = fields.ManyToManyField(SubjectResource, 'subjects')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()

class ParameterizedNoteResource(ModelResource):
    """
    A resource that requires the kwarg `param` to be
    passed by the URL pattern.
    """
    
    #def obj_get_list(self, bundle, **kwargs):
    #    param = kwargs['param']
    #    return super(ParameterizedNoteResource, self).obj_get_list(self, bundle, **kwargs)

    class Meta:
        resource_name = 'parameterized_notes'
        queryset = Note.objects.all()


api = Api(api_name='v1')
api.register(CustomNoteResource())
api.register(UserResource())
api.register(SubjectResource())

api2 = Api(api_name='v2')
api2.register(ParameterizedNoteResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
    (r'^parameterized/(?P<param>[a-z]+)/api/', include(api2.urls)),
)
