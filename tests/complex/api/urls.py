from django.conf.urls.defaults import *
from tastypie.api import Api
from complex.api.resources import PostResource, ProfileResource, CommentResource, UserResource, GroupResource


api = Api(api_name='v1')
api.register(PostResource(), canonical=True)
api.register(ProfileResource(), canonical=True)
api.register(CommentResource(), canonical=True)
api.register(UserResource(), canonical=True)
api.register(GroupResource(), canonical=True)

urlpatterns = api.urls
