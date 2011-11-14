import datetime
from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    author = models.ForeignKey(User, related_name='notes', blank=True, null=True)
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(Note, self).save(*args, **kwargs)
    
    def what_time_is_it(self):
        return datetime.datetime(2010, 4, 1, 0, 48)
    
    def get_absolute_url(self):
        return '/some/fake/path/%s/' % self.pk

    @property
    def my_property(self):
        return 'my_property'


class Subject(models.Model):
    notes = models.ManyToManyField(Note, related_name='subjects')
    name = models.CharField(max_length=255)
    url = models.URLField(verify_exists=False)
    created = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.name


class MediaBit(models.Model):
    note = models.ForeignKey(Note, related_name='media_bits')
    title = models.CharField(max_length=32)
    image = models.FileField(blank=True, null=True, upload_to='bits/')
    
    def __unicode__(self):
        return self.title
