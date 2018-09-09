.. _ref-fields:

===============
Resource Fields
===============

When designing an API, an important component is defining the representation
of the data you're presenting. Like Django models, you can control the
representation of a ``Resource`` using fields. There are a variety of fields
for various types of data.


Quick Start
===========

For the impatient::

  from tastypie import fields, utils
  from tastypie.resources import Resource
  from myapp.api.resources import ProfileResource, NoteResource


  class PersonResource(Resource):
      name = fields.CharField(attribute='name')
      age = fields.IntegerField(attribute='years_old', null=True)
      created = fields.DateTimeField(readonly=True, help_text='When the person was created', default=utils.now)
      is_active = fields.BooleanField(default=True)
      profile = fields.ToOneField(ProfileResource, 'profile')
      notes = fields.ToManyField(NoteResource, 'notes', full=True)


Standard Data Fields
====================

All standard data fields have a common base class ``ApiField`` which handles
the basic implementation details.

.. note::

  You should not use the ``ApiField`` class directly. Please use one of the
  subclasses that is more correct for your data.

Common Field Options
--------------------

All ``ApiField`` objects accept the following options.

``attribute``
~~~~~~~~~~~~~

.. attribute:: ApiField.attribute

A string naming an instance attribute of the object wrapped by the Resource. The
attribute will be accessed during the ``dehydrate`` or written during the ``hydrate``.

Defaults to ``None``, meaning data will be manually accessed.

``default``
~~~~~~~~~~~

.. attribute:: ApiField.default

Provides default data when the object being ``dehydrated``/``hydrated`` has no data on
the field.

Defaults to ``tastypie.fields.NOT_PROVIDED``.

``null``
~~~~~~~~

.. attribute:: ApiField.null

Indicates whether or not a ``None`` is allowable data on the field. Defaults to
``False``.

``blank``
~~~~~~~~~

.. attribute:: ApiField.blank

Indicates whether or not data may be omitted on the field. Defaults to ``False``.

This is useful for allowing the user to omit data that you can populate based
on the request, such as the ``user`` or ``site`` to associate a record with.

``readonly``
~~~~~~~~~~~~

.. attribute:: ApiField.readonly

Indicates whether the field is used during the ``hydrate`` or not. Defaults to ``False``.

``unique``
~~~~~~~~~~

.. attribute:: ApiField.unique

Indicates whether the field is a unique identifier for the object.

``help_text``
~~~~~~~~~~~~~

.. attribute:: ApiField.help_text

A human-readable description of the field exposed at the schema level.
Defaults to the per-Field definition.

``use_in``
~~~~~~~~~~

.. attribute:: ApiField.use_in

Optionally omit this field in list or detail views.  It can be either 'all',
'list', or 'detail' or a callable which accepts a bundle and returns a boolean
value.

Field Types
-----------

.. module:: tastypie.fields

``BooleanField``
----------------

A boolean field.

Covers both ``models.BooleanField`` and ``models.NullBooleanField``.

``CharField``
-------------

A text field of arbitrary length.

Covers both ``models.CharField`` and ``models.TextField``.

``DateField``
-------------

A date field.

``DateTimeField``
-----------------

A datetime field.

``DecimalField``
----------------

A decimal field.

``DictField``
-------------

A dictionary field.

``FileField``
-------------

A file-related field.

Covers both ``models.FileField`` and ``models.ImageField``.

``FloatField``
--------------

A floating point field.

``IntegerField``
----------------

An integer field.

Covers ``models.IntegerField``, ``models.PositiveIntegerField``,
``models.PositiveSmallIntegerField`` and ``models.SmallIntegerField``.

``ListField``
-------------

A list field.

``TimeField``
-------------

A time field.


Relationship Fields
===================

Provides access to data that is related within the database.

The ``RelatedField`` base class is not intended for direct use but provides
functionality that ``ToOneField`` and ``ToManyField`` build upon.

The contents of this field actually point to another ``Resource``,
rather than the related object. This allows the field to represent its data
in different ways.

The abstractions based around this are "leaky" in that, unlike the other
fields provided by ``tastypie``, these fields don't handle arbitrary objects
very well. The subclasses use Django's ORM layer to make things go, though
there is no ORM-specific code at this level.

Common Field Options
--------------------

In addition to the common attributes for all `ApiField`, relationship fields
accept the following.

``to``
~~~~~~

.. attribute:: RelatedField.to

The ``to`` argument should point to a ``Resource`` class, NOT to a ``Model``.
Required.

``full``
~~~~~~~~

.. attribute:: RelatedField.full

Indicates how the related ``Resource`` will appear post-``dehydrate``. If
``False``, the related ``Resource`` will appear as a URL to the endpoint of
that resource. If ``True``, the result of the sub-resource's ``dehydrate`` will
be included in full. You can further control post-``dehydrate`` behaviour when
requesting a resource or a list of resources by setting ``full_list`` and ``full_detail``.

``full_list``
~~~~~~~~~~~~~

.. attribute:: RelatedField.full_list

Indicates how the related ``Resource`` will appear post-``dehydrate`` when requesting a
list of resources. The value is one of ``True``, ``False`` or a callable that accepts a
bundle and returns ``True`` or ``False``. If ``False``, the related ``Resource`` will appear
as a URL to the endpoint of that resource if accessing a list of resources.  If ``True`` and ``full``
is also ``True``, the result of the sub-resource's ``dehydrate`` will be included in
full. Default is ``True``

``full_detail``
~~~~~~~~~~~~~~~

.. attribute:: RelatedField.full_detail

Indicates how the related ``Resource`` will appear post-``dehydrate`` when requesting a
single resource. The value is one of ``True``, ``False`` or a callable that accepts a
bundle and returns ``True`` or ``False``. If ``False``, the related ``Resource`` will appear
as a URL to the endpoint of that resource if accessing a specific resources. If ``True`` and ``full``
is also ``True``, the result of the sub-resource's ``dehydrate`` will be included
in full. Default is ``True``

``related_name``
~~~~~~~~~~~~~~~~

.. attribute:: RelatedField.related_name

Used to help automatically populate reverse relations when creating data.
Defaults to ``None``.

In order for this option to work correctly, there must be a field on the
other ``Resource`` with this as an ``attribute/instance_name``. Usually this
just means adding a reflecting ``ToOneField`` pointing back.

Example::

    class EntryResource(ModelResource):
        authors = fields.ToManyField('path.to.api.resources.AuthorResource', 'author_set', related_name='entry')

        class Meta:
            queryset = Entry.objects.all()
            resource_name = 'entry'

    class AuthorResource(ModelResource):
        entry = fields.ToOneField(EntryResource, 'entry')

        class Meta:
            queryset = Author.objects.all()
            resource_name = 'author'


Field Types
-----------

``ToOneField``
~~~~~~~~~~~~~~

Provides access to related data via foreign key.

This subclass requires Django's ORM layer to work properly.

``OneToOneField``
~~~~~~~~~~~~~~~~~

An alias to ``ToOneField`` for those who prefer to mirror ``django.db.models``.

``ForeignKey``
~~~~~~~~~~~~~~

An alias to ``ToOneField`` for those who prefer to mirror ``django.db.models``.

``ToManyField``
~~~~~~~~~~~~~~~

Provides access to related data via a join table.

This subclass requires Django's ORM layer to work properly.

This field also has special behavior when dealing with ``attribute`` in that
it can take a callable. For instance, if you need to filter the reverse
relation, you can do something like::

    subjects = fields.ToManyField(SubjectResource, attribute=lambda bundle: Subject.objects.filter(notes=bundle.obj, name__startswith='Personal'))

The callable should either return an iterable of objects or ``None``.

Note that the ``hydrate`` portions of this field are quite different than
any other field. ``hydrate_m2m`` actually handles the data and relations.
This is due to the way Django implements M2M relationships.

``ManyToManyField``
~~~~~~~~~~~~~~~~~~~

An alias to ``ToManyField`` for those who prefer to mirror ``django.db.models``.

``OneToManyField``
~~~~~~~~~~~~~~~~~~

An alias to ``ToManyField`` for those who prefer to mirror ``django.db.models``.
