from django.contrib.auth.models import User
from tastypie import fields
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from basic.models import Note, AnnotatedNote, UserForm
from django import forms
from tastypie.validation import FormValidation

# NOTES:
# model defaults don't matter since we are not rendering a form, if you want to use a default exclude the field.


class UserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = User.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=UserForm)

class AnnotatedNoteForm(forms.ModelForm):

    class Meta:
        model = AnnotatedNote
        exclude = ('note',)

    # Refuse any annotations including '42'
    def clean_annotations(self):
        data = self.cleaned_data["annotations"]
        if isinstance(data, basestring) and "42" in data:
            raise forms.ValidationError("You cannot use annotations including the string '42'")
        else:
            return data

class AnnotatedNoteResource(ModelResource):

    class Meta:
        resource_name = 'annotated'
        queryset = AnnotatedNote.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=AnnotatedNoteForm)

class NoteForm(forms.ModelForm):

    class Meta:
        model = Note
        exclude = ('user', 'created', 'updated')

class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    annotated = fields.ForeignKey(AnnotatedNoteResource, 'annotated', related_name='note', null=True, full=True)

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()
        authorization = Authorization()
        validation = FormValidation(form_class=NoteForm)
        filtering = {
            "created": ALL
            }
