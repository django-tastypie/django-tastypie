from django import forms
from core.models import Note


class NoteForm(forms.ModelForm):
    foobaz = forms.CharField()

    class Meta:
        model = Note


class VeryCustomNoteForm(NoteForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'created', 'is_active', 'foobaz']


# Notes:
# * VeryCustomNoteForm will ONLY have the four listed fields.
# * VeryCustomNoteForm does NOT inherit the ``foobaz`` field from it's
#   parent class (unless manually specified).
