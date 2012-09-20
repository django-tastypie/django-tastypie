import datetime
from django.contrib.auth.models import User
from django.db import models
from tastypie.utils import now, aware_datetime


class DateRecord(models.Model):
    date = models.DateField()
    username = models.CharField(max_length=20)
    message = models.CharField(max_length=20)


class Note(models.Model):
    author = models.ForeignKey(User, related_name='notes', blank=True, null=True)
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(default=now)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.updated = now()
        return super(Note, self).save(*args, **kwargs)

    def what_time_is_it(self):
        return aware_datetime(2010, 4, 1, 0, 48)

    def get_absolute_url(self):
        return '/some/fake/path/%s/' % self.pk

    @property
    def my_property(self):
        return 'my_property'

class NoteWithEditor(Note):
    editor = models.ForeignKey(User, related_name='notes_edited')

class Subject(models.Model):
    notes = models.ManyToManyField(Note, related_name='subjects')
    name = models.CharField(max_length=255)
    url = models.URLField()
    created = models.DateTimeField(default=now)

    def __unicode__(self):
        return self.name


class MediaBit(models.Model):
    note = models.ForeignKey(Note, related_name='media_bits')
    title = models.CharField(max_length=32)
    image = models.FileField(blank=True, null=True, upload_to='bits/')

    def __unicode__(self):
        return self.title


class AutoNowNote(models.Model):
    # Purposely a bit more complex to test correct introspection.
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=now, null=True)
    updated = models.DateTimeField(auto_now=now)

    def __unicode__(self):
        return self.title


class Counter(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)
    count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.name
