.. _authorization-reference:

Authorization Reference
***********************

Authorization is the component needed to verify what someone can do with the
resources within an API.

Authorization answers the question "Is permission granted for this user to take
this action?" This usually involves checking permissions such as
Create/Read/Update/Delete access, or putting limits on what data the user
can access.


_authorization-reference#authorization-methods:

``Authorization`` Methods
=========================

.. _authorization-reference#read-list-method:

``read_list``
-------------

.. method:: Authorization.read_list(self, object_list, bundle)

Returns a list of all the objects a user is allowed to read.

Should return an empty list if none are allowed.

Returns the entire list by default.


.. _authorization-reference#read-detail-method:

``read_detail``
---------------

.. method:: Authorization.read_detail(self, object_list, bundle)

Returns either ``True`` if the user is allowed to read the object in question or
throw ``Unauthorized`` if they are not.

Returns ``True`` by default.


.. _authorization-reference#create-list-method:

``create_list``
---------------

.. method:: Authorization.create_list(self, object_list, bundle)

Unimplemented, as Tastypie never creates entire new lists, but present for
consistency & possible extension.


.. _authorization-reference#create-detail-method:

``create_detail``
-----------------

.. method:: Authorization.create_detail(self, object_list, bundle)

Returns either ``True`` if the user is allowed to create the object in question
or throw ``Unauthorized`` if they are not.

Returns ``True`` by default.


.. _authorization-reference#update-list-method:

``update_list``
---------------

.. method:: Authorization.update_list(self, object_list, bundle)

Returns a list of all the objects a user is allowed to update.

Should return an empty list if none are allowed.

Returns the entire list by default.


.. _authorization-reference#update-detail-method:

``update_detail``
-----------------

.. method:: Authorization.update_detail(self, object_list, bundle)

Returns either ``True`` if the user is allowed to update the object in question
or throw ``Unauthorized`` if they are not.

Returns ``True`` by default.


.. _authorization-reference#delete-list-method:

``delete_list``
---------------

.. method:: Authorization.delete_list(self, object_list, bundle)

Returns a list of all the objects a user is allowed to delete.

Should return an empty list if none are allowed.

Returns the entire list by default.


.. _authorization-reference#delete-detail-method:

``delete_detail``
-----------------

.. method:: Authorization.delete_detail(self, object_list, bundle)

Returns either ``True`` if the user is allowed to delete the object in question
or throw ``Unauthorized`` if they are not.

Returns ``True`` by default.


.. _authorization-reference#authorization-classes:

Authorization Classes
=====================

Tastypie ships with the following ``Authorization`` classes:


.. _authorization-reference#authorization-class:

``Authorization``
-----------------

The no-op authorization option, no permissions checks are performed.

.. warning::

  This is a potentially dangerous option, as it means *ANY* recognized user can
  modify *ANY* data they encounter in the API. Be careful who you trust.


.. _authorization-reference#readonlyauthorization-class:

``ReadOnlyAuthorization``
-------------------------

This authorization class only permits reading data, regardless of what the
``Resource`` might think is allowed. This is the default ``Authorization`` class
and the safe option.


.. _authorization-reference#djangoauthorization-class:

``DjangoAuthorization``
-----------------------

The most advanced form of authorization, this checks the permission a user has
granted to them (via ``django.contrib.auth.models.Permission``). In conjunction
with the admin, this is a very effective means of control.
