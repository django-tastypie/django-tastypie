from django.conf.urls.defaults import *
from tastypie.api import Api
from related_resource.api.resources import NoteResource, UserResource, \
        CategoryResource, TagResource, TaggableTagResource, TaggableResource, \
        ExtraDataResource, GenericTagResource
from tastypie.resources import ContentTypeResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(CategoryResource(), canonical=True)
api.register(TagResource(), canonical=True)
api.register(TaggableResource(), canonical=True)
api.register(TaggableTagResource(), canonical=True)
api.register(ExtraDataResource(), canonical=True)
api.register(GenericTagResource(), canonical=True)
api.register(ContentTypeResource())
urlpatterns = api.urls
