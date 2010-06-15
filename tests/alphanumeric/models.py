import datetime
from django.db import models


class Product(models.Model):
    artnr = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=32, null=False, blank=True, default='')
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return "%s - %s" % (self.artnr, self.name)
    
    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(Product, self).save(*args, **kwargs)
