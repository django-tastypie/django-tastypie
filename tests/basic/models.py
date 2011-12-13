import datetime
from django.contrib.auth.models import User
from django.db import models
from django import forms


class Note(models.Model):
    user = models.ForeignKey(User, related_name='notes')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(Note, self).save(*args, **kwargs)

class AnnotatedNote(models.Model):
    note = models.OneToOneField(Note, related_name='annotated', null=True)
    annotations = models.TextField()
    
    def __unicode__(self):
        return u"Annotated %s" % self.note.title

class UserForm(forms.ModelForm):
    # XXX: A better fix is probably to not emit fractional seconds in the
    # default serializers. In the meantime, be sure we accept what we output.
    formats = ['%Y-%m-%dT%H:%M:%S.%f','%Y-%m-%dT%H:%M:%S'] 
    date_joined = forms.DateTimeField(input_formats=formats) 
    last_login = forms.DateTimeField(input_formats=formats) 
    class Meta: 
        model = User
