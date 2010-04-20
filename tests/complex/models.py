import datetime
from django.contrib.auth.models import User
from django.contrib.comments.models import Comment
from django.contrib.contenttypes import generic
from django.db import models


class Post(models.Model):
    user = models.ForeignKey(User, related_name='notes')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)
    comments = generic.GenericRelation(Comment, content_type_field="content_type", object_id_field="object_pk")

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(Note, self).save(*args, **kwargs)


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
    file_path = models.FilePathField()
    avatar = models.ImageField(upload_to='avatars')
    ip = models.IPAddressField()
    rocks_da_house = models.NullBooleanField()
    name_slug = models.SlugField()
    bio = models.TextField()
    homepage = models.URLField()

    def __unicode__(self):
        return "%s's profile" % self.user
