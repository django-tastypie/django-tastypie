.. ref-bundle:

=======
Bundles
=======


What Are Bundles?
=================

Bundles are a small abstraction that allow Tastypie to pass data between
resources. This allows us not to depend on passing ``request`` to every single
method (especially in places where this would be overkill). It also allows
resources to work with data coming into the application paired together with
an unsaved instance of the object in question. Finally, it aids in keeping
Tastypie more thread-safe.

Think of it as package of user data & an object instance (either of which are
optionally present).


Attributes
==========

All data within a bundle can be optional, especially depending on how it's
being used. If you write custom code using ``Bundle``, make sure appropriate
guards are in place.

``obj``
-------

Either a Python object or ``None``.

Usually a Django model, though it may/may not have been saved already.

``data``
--------

Always a plain Python dictionary of data. If not provided, it will be empty.

``request``
-----------

Either the Django ``request`` that's part of the issued request or an empty
``HttpRequest`` if it wasn't provided.

``related_obj``
---------------

Either another "parent" Python object or ``None``.

Useful when handling one-to-many relations. Used in conjunction with
``related_name``.

``related_name``
----------------

Either a Python string name of an attribute or ``None``.

Useful when handling one-to-many relations. Used in conjunction with
``related_obj``.
