from tastypie.api import Api
from basic.api.resources import NoteResource, UserResource, BustedResource,\
    CachedUserResource, PublicCachedUserResource, PrivateCachedUserResource,\
    CacheDisabledUserResource, SlugBasedNoteResource, SessionUserResource


api = Api(api_name='v1')
api.register(NoteResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(CachedUserResource(), canonical=True)
api.register(CacheDisabledUserResource(), canonical=True)
api.register(PublicCachedUserResource(), canonical=True)
api.register(PrivateCachedUserResource(), canonical=True)

v2_api = Api(api_name='v2')
v2_api.register(BustedResource(), canonical=True)
v2_api.register(SlugBasedNoteResource())
v2_api.register(SessionUserResource())

urlpatterns = v2_api.urls + api.urls
