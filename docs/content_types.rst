.. _ref-content_types:

===================================
ContentTypes and GenericForeignKeys
===================================

`Content Types`_ and GenericForeignKeys are for relationships where the model on
one end is not defined by the model's schema.

.. _Content Types: https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/

If you're using GenericForeignKeys in django, you can use a
GenericForeignKeyField in Tastypie.

Usage
=====

Here's an example model with a GenericForeignKey taken from the Django docs::

    from django.db import models
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes import generic

    class TaggedItem(models.Model):
        tag = models.SlugField()
        content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        object_id = models.PositiveIntegerField()
        content_object = generic.GenericForeignKey('content_type', 'object_id')

        def __unicode__(self):
            return self.tag

A simple ModelResource for this model might look like this::

    from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
    from tastypie.resources import ModelResource

    from .models import Note, Quote, TaggedItem


    class QuoteResource(ModelResource):

        class Meta:
            resource_name = 'quotes'
            queryset = Quote.objects.all()


    class NoteResource(ModelResource):

        class Meta:
            resource_name = 'notes'
            queryset = Note.objects.all()


    class TaggedItemResource(ModelResource):
        content_object = GenericForeignKeyField({
            Note: NoteResource,
            Quote: QuoteResource
        }, 'content_object')

        class Meta:
            resource_name = 'tagged_items'
            queryset = TaggedItem.objects.all()

A ModelResource that is to be used as a relation to a GenericForeignKeyField
must also be registered to the Api instance defined in your URLconf in order
to provide a reverse uri for lookups.

Like ToOneField, you must add your GenericForeignKey attribute to your
ModelResource definition. It will not be added automatically like most other
field or attribute types. When you define it, you must also define the other
models and match them to their resources in a dictionary, and pass that as the
first argument, the second argument is the name of the attribute on the model
that holds the GenericForeignKey.
