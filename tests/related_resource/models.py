from django.contrib.auth.models import User
from django.db import models


# A self-referrential model to test regressions.
class Category(models.Model):
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
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
        null=True,
        blank=True,  # needed at creation time
        on_delete=models.CASCADE,
    )
    taggable = models.ForeignKey(
        'Taggable',
        related_name='taggabletags',
        null=True,
        blank=True,  # needed at creation time
        on_delete=models.CASCADE,
    )
    extra = models.IntegerField(default=0)  # extra data about the relationship


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
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    def __unicode__(self):
        return u"%s" % (self.name)


class Address(models.Model):
    line = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s" % (self.line)


class Company(models.Model):
    name = models.CharField(max_length=32)
    address = models.ForeignKey(Address, null=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return u"%s" % (self.name)


class Product(models.Model):
    name = models.CharField(max_length=32)
    producer = models.ForeignKey(Company, related_name="products",
                                 on_delete=models.CASCADE)

    def __unicode__(self):
        return u"%s" % (self.name)


class Person(models.Model):
    name = models.CharField(max_length=32)
    company = models.ForeignKey(Company, related_name="employees", null=True,
                                on_delete=models.CASCADE)

    def __unicode__(self):
        return u"%s" % (self.name)


class DogHouse(models.Model):
    color = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s" % (self.color)


class Dog(models.Model):
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(Person, related_name="dogs",
                              on_delete=models.CASCADE)
    house = models.ForeignKey(DogHouse, related_name="dogs", null=True,
                              on_delete=models.CASCADE)

    def __unicode__(self):
        return u"%s" % (self.name)


class Bone(models.Model):
    dog = models.ForeignKey(Dog, related_name='bones', null=True,
                            on_delete=models.CASCADE)
    color = models.CharField(max_length=32)

    def __unicode__(self):
        return u"%s" % (self.color)


class Forum(models.Model):
    moderators = models.ManyToManyField(User, related_name='forums_moderated')
    members = models.ManyToManyField(User, related_name='forums_member')


class Label(models.Model):
    name = models.CharField(max_length=32)


class Job(models.Model):
    name = models.CharField(max_length=200)


class Payment(models.Model):
    scheduled = models.DateTimeField()
    job = models.OneToOneField(Job, related_name="payment", null=True,
                               on_delete=models.CASCADE)


class Post(models.Model):
    name = models.CharField(max_length=200)
    label = models.ManyToManyField(Label)


class Order(models.Model):
    name = models.CharField(max_length=200)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items",
                              on_delete=models.CASCADE)
    product = models.CharField(max_length=200)


class ContactGroup(models.Model):
    name = models.CharField(max_length=75, blank=True,
        help_text="Contact first name.")

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return u'%s' % self.name


class Contact(models.Model):
    name = models.CharField(max_length=255)
    groups = models.ManyToManyField(
        ContactGroup,
        related_name='members',
        blank=True,
        help_text="The Contact Groups this Contact belongs to."
    )

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return u'%s' % self.name
