from tastypie.fields import CharField, ForeignKey, ManyToManyField, OneToOneField, OneToManyField
from tastypie.representations.models import ModelRepresentation
from complex.models import Post, Profile
from django.contrib.auth.models import User, Group
from django.contrib.comments.models import Comment


class ProfileRepresentation(ModelRepresentation):
    class Meta:
        queryset = Profile.objects.all()


class CommentRepresentation(ModelRepresentation):
    class Meta:
        queryset = Comment.objects.all()


class GroupRepresentation(ModelRepresentation):
    class Meta:
        queryset = Group.objects.all()


class UserRepresentation(ModelRepresentation):
    groups = ManyToManyField(GroupRepresentation, 'groups', full_repr=True)
    profile = OneToOneField(ProfileRepresentation, 'profile', full_repr=True)
    class Meta:
        queryset = User.objects.all()


class PostRepresentation(ModelRepresentation):
    user = ForeignKey(UserRepresentation, 'user')
    comments = OneToManyField(CommentRepresentation, 'comments', full_repr=False)
    class Meta:
        queryset = Post.objects.all()
