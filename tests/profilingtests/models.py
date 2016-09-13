from django.contrib.auth.models import User
from django.db import models
from tastypie.utils import now, aware_datetime


class Note(models.Model):
    author = models.ForeignKey(User, blank=True, null=True,
                               on_delete=models.CASCADE)
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
