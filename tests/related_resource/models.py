from django.db import models


# A self-referrential model to test regressions.
class Category(models.Model):
    parent = models.ForeignKey('self', null=True)
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.parent)


# A taggable model. Just that.
class Taggable(models.Model):
    name = models.CharField(max_length=32)


# Explicit intermediary 'through' table
class TaggableTag(models.Model):
    tag = models.ForeignKey(
            'Tag',
            related_name='taggabletags',
            null=True, blank=True, # needed at creation time
        )
    taggable = models.ForeignKey(
            'Taggable',
            related_name='taggabletags',
            null=True, blank=True, # needed at creation time
    )


# Tags to Taggable model through explicit M2M table
class Tag(models.Model):
    name = models.CharField(max_length=32)
    tagged = models.ManyToManyField(
        'Taggable',
        through='TaggableTag',
        related_name='tags',
    )

    def __unicode__(self):
        return u"%s" % (self.name)


# A model that contains additional data for Tag
class ExtraData(models.Model):
    name = models.CharField(max_length=32)
    tag = models.OneToOneField(
        'Tag',
        related_name='extradata',
        null=True, blank=True,
    )

    def __unicode__(self):
        return u"%s" % (self.name)


class Company(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s" % (self.name)


class Person(models.Model):
    name = models.CharField(max_length=32)
    company = models.ForeignKey(Company, related_name="employees")

    def __unicode__(self):
        return u"%s" % (self.name)

class DogHouse(models.Model):
    color = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s" % (self.color)


class Dog(models.Model):
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(Person, related_name="dogs")
    house = models.ForeignKey(DogHouse, related_name="dogs")

    def __unicode__(self):
        return u"%s" % (self.name)

    