import datetime
import os
from django.contrib.auth.models import User
from django.contrib.comments.models import Comment
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import models
from django.db.models import signals, get_models
from django.conf import settings

from tastypie.utils import now

try:
    import PIL
except:
    PIL = None

class Post(models.Model):
    user = models.ForeignKey(User, related_name='notes')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(default=now)
    comments = generic.GenericRelation(Comment, content_type_field="content_type", object_id_field="object_pk")

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.updated = now()
        return super(Post, self).save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User)
    email = models.EmailField()
    active = models.BooleanField()
    favorite_color = models.CharField(max_length=255)
    favorite_numbers = models.CommaSeparatedIntegerField(max_length=5)
    favorite_number = models.IntegerField()
    age = models.PositiveSmallIntegerField()
    favorite_small_number = models.SmallIntegerField()
    height = models.PositiveIntegerField()
    weight = models.FloatField()
    balance = models.DecimalField(decimal_places=2, max_digits=6)
    date_joined = models.DateField()
    time_joined = models.TimeField()
    datetime_joined = models.DateTimeField()
    document = models.FileField(upload_to='documents')
    file_path = models.FilePathField(path=settings.MEDIA_ROOT)
    ip = models.IPAddressField()
    rocks_da_house = models.NullBooleanField()
    name_slug = models.SlugField()
    bio = models.TextField()
    homepage = models.URLField()
    if PIL:
        avatar = models.ImageField(upload_to='avatars')
    else:
        avatar = models.FileField(upload_to='avatars')

    def __unicode__(self):
        return "%s's profile" % self.user

