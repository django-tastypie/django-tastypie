import time
from django.db import models


class ApiAccess(models.Model):
    identifier = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, default='')
    request_method = models.CharField(max_length=10, blank=True, default='')
    accessed = models.PositiveIntegerField()
    
    def __unicode__(self):
        return u"%s @ %s" % (self.identifer, self.accessed)
    
    def save(self, *args, **kwargs):
        self.accessed = int(time.time())
        return super(ApiAccess, self).save(*args, **kwargs)
