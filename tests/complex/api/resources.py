from tastypie.resources import Resource
from complex.api.representations import (
    PostRepresentation,
    ProfileRepresentation,
    CommentRepresentation,
    UserRepresentation,
    GroupRepresentation,
)

class PostResource(Resource):
    representation = PostRepresentation
    resource_name = 'posts'

class ProfileResource(Resource):
    representation = ProfileRepresentation
    resource_name = 'profiles'

class CommentResource(Resource):
    representation = CommentRepresentation
    resource_name = 'comments'

class UserResource(Resource):
    representation = UserRepresentation
    resource_name = 'users'

class GroupResource(Resource):
    representation = GroupRepresentation
    resource_name = 'groups'
