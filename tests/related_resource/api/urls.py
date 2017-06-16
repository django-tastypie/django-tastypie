from tastypie.api import Api

from related_resource.api.resources import NoteResource, UserResource,\
    CategoryResource, TagResource, TaggableTagResource, TaggableResource,\
    ExtraDataResource, FreshNoteResource, FreshMediaBitResource,\
    ForumResource, CompanyResource, ProductResource, AddressResource,\
    PersonResource, DogResource, DogHouseResource, BoneResource,\
    LabelResource, PostResource, OrderResource, OrderItemResource,\
    NoteWithUpdatableUserResource, ContactResource, ContactGroupResource


api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(NoteWithUpdatableUserResource(), canonical=True)
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
api.register(OrderResource(), canonical=True)
api.register(OrderItemResource(), canonical=True)
api.register(ContactResource(), canonical=True)
api.register(ContactGroupResource(), canonical=True)

urlpatterns = api.urls
