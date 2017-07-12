from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models

from tastypie.utils import now

if settings.DJANGO_VERSION >= settings.DJANGO_20:
    GeoManager = models.Manager
else:
    GeoManager = models.GeoManager


class GeoNote(models.Model):
    user = models.ForeignKey(User, related_name='notes',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(default=now)

    points = models.MultiPointField(null=True, blank=True)
    lines = models.MultiLineStringField(null=True, blank=True)
    polys = models.MultiPolygonField(null=True, blank=True)

    objects = GeoManager()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.updated = now()
        return super(GeoNote, self).save(*args, **kwargs)


class AnnotatedGeoNote(models.Model):
    note = models.OneToOneField(GeoNote, related_name='annotated', null=True,
                                on_delete=models.CASCADE)
    annotations = models.TextField()

    def __unicode__(self):
        return u"Annotated %s" % self.note.title
