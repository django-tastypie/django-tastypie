from tastypie.fields import CharField
from tastypie.representations.models import ModelRepresentation
from complex.models import Post, Profile
from django.contrib.auth.models import User, Group
from django.contrib.comments.models import Comment

class RepresentationWithURI(ModelRepresentation):
    resource_uri = CharField()

    # FIXME: This should probably get significantly more automated.
    def dehydrate_resource_uri(self, obj):
        return self.get_resource_uri()

class PostRepresentation(RepresentationWithURI):
    class Meta:
        queryset = Post.objects.all()

class ProfileRepresentation(RepresentationWithURI):
    class Meta:
        queryset = Profile.objects.all()

class CommentRepresentation(RepresentationWithURI):
    class Meta:
        queryset = Comment.objects.all()

class UserRepresentation(RepresentationWithURI):
    class Meta:
        queryset = User.objects.all()

class GroupRepresentation(RepresentationWithURI):
    class Meta:
        queryset = Group.objects.all()
