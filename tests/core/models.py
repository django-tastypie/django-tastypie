import datetime
from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    author = models.ForeignKey(User, related_name='notes', blank=True, null=True)
    title = models.CharField(max_length=100)
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
    
    def what_time_is_it(self):
        return datetime.datetime(2010, 4, 1, 0, 48)
