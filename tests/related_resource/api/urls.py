try:
    from django.conf.urls import *
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import *

from tastypie.api import Api

from related_resource.api.resources import AddressResource, BoneResource, \
    CategoryResource, CompanyResource, ContactResource, ContactGroupResource, \
    DogResource, DogHouseResource, ExtraDataResource, FreshNoteResource, \
    FreshMediaBitResource, ForumResource, LabelResource, NoteResource, PersonResource, \
    PostResource, ProductResource, TagResource, TaggableResource, \
    TaggableTagResource, UserResource

api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(CategoryResource(), canonical=True)
api.register(TagResource(), canonical=True)
api.register(TaggableResource(), canonical=True)
api.register(TaggableTagResource(), canonical=True)
api.register(ExtraDataResource(), canonical=True)
api.register(FreshNoteResource(), canonical=True)
api.register(FreshMediaBitResource(), canonical=True)
api.register(ForumResource(), canonical=True)
api.register(CompanyResource(), canonical=True)
api.register(ProductResource(), canonical=True)
api.register(AddressResource(), canonical=True)
api.register(PersonResource(), canonical=True)
api.register(DogResource(), canonical=True)
api.register(DogHouseResource(), canonical=True)
api.register(BoneResource(), canonical=True)
api.register(PostResource(), canonical=True)
api.register(LabelResource(), canonical=True)
api.register(ContactResource(), canonical=True)
api.register(ContactGroupResource(), canonical=True)

urlpatterns = api.urls
