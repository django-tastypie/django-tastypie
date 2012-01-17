from django.contrib.auth.models import User
from tastypie import fields
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.validation import FormValidation
from basic.models import Note, UserForm


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=UserForm)


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        filtering = {
            "created": ALL
            }
        
