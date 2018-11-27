from django.db import models
from tastypie.utils import now


class Product(models.Model):
    artnr = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=32, null=False, blank=True, default='')
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(default=now)

    def __unicode__(self):
        return "%s - %s" % (self.artnr, self.name)

    def save(self, *args, **kwargs):
        self.updated = now()
        return super(Product, self).save(*args, **kwargs)
