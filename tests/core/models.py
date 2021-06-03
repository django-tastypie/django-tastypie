from itertools import count
import uuid

from django.db import models

from tastypie.utils import now, aware_datetime
from tastypie.compat import AUTH_USER_MODEL


class DateRecord(models.Model):
    date = models.DateField()
    username = models.CharField(max_length=20)
    message = models.CharField(max_length=20)

    class Meta:
        app_label = 'core'


class Note(models.Model):
    author = models.ForeignKey(AUTH_USER_MODEL, related_name='notes', blank=True,
                               null=True, on_delete=models.CASCADE)
    title = models.CharField("The Title", max_length=100)
    slug = models.SlugField()
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, blank=True)
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

    class Meta:
        app_label = 'core'


class NoteWithEditor(Note):
    editor = models.ForeignKey(AUTH_USER_MODEL, related_name='notes_edited',
                               on_delete=models.CASCADE)

    class Meta:
        app_label = 'core'


class Subject(models.Model):
    notes = models.ManyToManyField(Note, related_name='subjects')
    name = models.CharField(max_length=255)
    url = models.URLField()
    created = models.DateTimeField(default=now)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'core'


class MediaBit(models.Model):
    note = models.ForeignKey(Note, related_name='media_bits',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=32)
    image = models.FileField(blank=True, null=True, upload_to='bits/')

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = 'core'


class AutoNowNote(models.Model):
    # Purposely a bit more complex to test correct introspection.
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    created = models.DateTimeField(auto_now_add=now, null=True)
    updated = models.DateTimeField(auto_now=now)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = 'core'


class BigAutoNowModel(models.Model):
    id = models.BigAutoField(primary_key=True)

    class Meta:
        app_label = 'core'


class Counter(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)
    count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'core'


int_source = count(1)


def get_next():
    return next(int_source)


class MyDefaultPKModel(models.Model):
    id = models.IntegerField(primary_key=True, default=get_next, editable=False)
    content = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'core'


class MyUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anotheruuid = models.UUIDField(default=uuid.uuid4)
    content = models.TextField(blank=True, default='')
    order = models.IntegerField(default=0, blank=True)

    class Meta:
        ordering = ('order',)
        app_label = 'core'


class MyRelatedUUIDModel(models.Model):
    myuuidmodels = models.ManyToManyField(MyUUIDModel)
    content = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'core'
