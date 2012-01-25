from django.contrib.auth.models import User
from tastypie import fields
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from basic.models import Note, AnnotatedNote
from django import forms
from tastypie.validation import FormValidation


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()

class AnnotatedNoteForm(forms.ModelForm):

    class Meta:
        model = AnnotatedNote

class AnnotatedNoteResource(ModelResource):

    class Meta:
        resource_name = 'annotated'
        queryset = AnnotatedNote.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=AnnotatedNoteForm)

class NoteForm(forms.ModelForm):

    class Meta:
        model = Note

class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    annotated_note = fields.ForeignKey(AnnotatedNote, 'annotated', null=True)

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=NoteForm)
        filtering = {
            "created": ALL
            }

