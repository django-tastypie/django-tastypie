import datetime
from django.contrib.auth.models import User
from django.db import models
from tastypie.utils import now

class Note(models.Model):
    user = models.ForeignKey(User, related_name='notes')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(default=now)

    def __unicode__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.updated = now()
        return super(Note, self).save(*args, **kwargs)

class AnnotatedNote(models.Model):
    note = models.OneToOneField(Note, related_name='annotated', null=True)
    annotations = models.TextField()
    
    def __unicode__(self):
        return u"Annotated %s" % self.note.title
