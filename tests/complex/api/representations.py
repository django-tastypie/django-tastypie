from tastypie.fields import CharField
from tastypie.representations.models import ModelRepresentation
from complex.models import Post, Profile
from django.contrib.auth.models import User, Group
from django.contrib.comments.models import Comment


class PostRepresentation(ModelRepresentation):
    class Meta:
        queryset = Post.objects.all()


class ProfileRepresentation(ModelRepresentation):
    class Meta:
        queryset = Profile.objects.all()


class CommentRepresentation(ModelRepresentation):
    class Meta:
        queryset = Comment.objects.all()


class UserRepresentation(ModelRepresentation):
    class Meta:
        queryset = User.objects.all()


class GroupRepresentation(ModelRepresentation):
    class Meta:
        queryset = Group.objects.all()
