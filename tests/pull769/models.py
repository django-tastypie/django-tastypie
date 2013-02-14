from django.db import models


class Simple(models.Model):
    name = models.CharField(max_length=100)


class Related(models.Model):
    name = models.CharField(max_length=100)
    simple = models.ForeignKey(Simple, related_name='related', verbose_name='simple', null=False, blank=False)
