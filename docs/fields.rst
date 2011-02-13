.. _ref-fields:

==================
Resource Fields
==================

Like Django models, a Tastypie Resource has Fields that map to specific data types. Here is what you can do with them.

Standard Data Fields
=====================

Common Field Options
####################
All ``ApiField`` objects accept the following options.

``attribute``
------------------
.. attribute:: ApiField.attribute

A string naming an instance attribute of the object wrapped by the Resource. The
attribute will be accessed during the ``dehydrate`` or or written during the ``hydrate``.

Defaults to ``None``, meaning data will be manually accessed.

``default``
------------------
.. attribute:: ApiField.default

Provides default data when the object being ``dehydrated``/``hydrated`` has no data on
the field.

Defaults to ``tastypie.fields.NOT_PROVIDED``.

``null``
------------------
.. attribute:: ApiField.null

Indicates whether or not a ``None`` is allowable data on the field. Defaults to
``False``.

``readonly``
------------------
.. attribute:: ApiField.readonly

Indicates whether the field is used during the ``hydrate`` or not. Defaults to ``False``.

``unique``
------------------
.. attribute:: ApiField.unique

Indicates whether the field is a unique identifier for the object.

``help_text``
------------------
.. attribute:: ApiField.help_text

A human-readable description of the field exposed at the schema level.
Defaults to the per-Field definition.


Field Types
####################
.. module:: tastypie.fields

.. autoclass:: ApiField(attribute=None, default=NOT_PROVIDED, null=False, readonly=False, unique=False, help_text=None)
    :members:
    
    The parent class of all fields. Do not use this directly. Other fields inherit these properties and methods.

``BooleanField``
--------------------
.. autoclass:: BooleanField(**options)
    :members:

``CharField``
--------------------
.. autoclass:: CharField(**options)
    :members:

``DateField``
--------------------
.. autoclass:: DateField(**options)
    :members:

``DateTimeField``
--------------------
.. autoclass:: DateTimeField(**options)
    :members:

``FileField``
--------------------
.. autoclass:: FileField(**options)
    :members:

``FloatField``
--------------------
.. autoclass:: FloatField(**options)
    :members:

``IntegerField``
--------------------
.. autoclass:: IntegerField(**options)
    :members:

Relationship Fields
=====================

Common Field Options
####################
In addition to the common attributes for all `ApiField`, relationship fields accept the following.

``to``
--------------------
.. attribute:: RelatedField.to

The ``to`` argument should point to a ``Resource`` class, NOT to a ``Model``.
Required.

``full``
--------------------
.. attribute:: RelatedField.full

Indicates how the related ``Resource`` will appear post-``dehydrate``. If
``False``, the related ``Resource`` will appear as a URL to the endpoint of
that resource. If ``True``, the result of the sub-resource's ``dehydrate`` will
be included in full.

``related_name``
--------------------
.. attribute:: RelatedField.related_name

Currently unused, as unlike Django's ORM layer, reverse relations between
``Resource`` classes are not automatically created. Defaults to ``None``.

Field Types
####################

.. autoclass:: RelatedField(to, attribute, full=False, **options)
    :members:

``ToOneField``
--------------------
.. autoclass:: ToOneField(to, attribute, full=False, **options)
    :members:

``OneToOneField``
--------------------
.. autoclass:: OneToOneField(to, attribute, full=False, **options)
    :members:

``ForeignKey``
--------------------
.. autoclass:: ForeignKey(to, attribute, full=False, **options)
    :members:

``ToManyField``
--------------------
.. autoclass:: ToManyField(to, attribute, full=False, **options)
    :members:

``ManyToManyField``
--------------------
.. autoclass:: ManyToManyField(to, attribute, full=False, **options)
    :members:

``OneToManyField``
--------------------
.. autoclass:: OneToManyField(to, attribute, full=False, **options)
    :members:
