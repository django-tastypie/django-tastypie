from django.contrib.auth.models import User, Group
from django.contrib.comments.models import Comment
from tastypie.fields import CharField, ForeignKey, ManyToManyField, OneToOneField, OneToManyField
from tastypie.resources import ModelResource
from complex.models import Post, Profile


class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'profiles'


class CommentResource(ModelResource):
    class Meta:
        queryset = Comment.objects.all()
        resource_name = 'comments'


class GroupResource(ModelResource):
    class Meta:
        queryset = Group.objects.all()
        resource_name = 'groups'


class UserResource(ModelResource):
    groups = ManyToManyField(GroupResource, 'groups', full=True)
    profile = OneToOneField(ProfileResource, 'profile', full=True)
    
    class Meta:
        queryset = User.objects.all()
        resource_name = 'users'


class PostResource(ModelResource):
    user = ForeignKey(UserResource, 'user')
    comments = OneToManyField(CommentResource, 'comments', full=False)
    
    class Meta:
        queryset = Post.objects.all()
        resource_name = 'posts'
