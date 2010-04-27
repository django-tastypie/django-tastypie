from tastypie.fields import CharField, ForeignKey
from tastypie.representations.models import ModelRepresentation
from basic.models import Note
from django.contrib.auth.models import User


class UserRepresentation(ModelRepresentation):
    class Meta:
        queryset = User.objects.all()


class NoteRepresentation(ModelRepresentation):
    user = ForeignKey(UserRepresentation, 'user')
    class Meta:
        queryset = Note.objects.all()
