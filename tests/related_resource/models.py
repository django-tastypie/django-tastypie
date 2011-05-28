from django.db import models


# A self-referrential model to test regressions.
class Category(models.Model):
    parent = models.ForeignKey('self', null=True)
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.parent)

