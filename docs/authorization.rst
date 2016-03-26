.. _authorization:

=============
Authorization
=============

Authorization is the component needed to verify what someone can do with
the resources within an API.

Authorization answers the question "Is permission granted for this user to take
this action?" This usually involves checking permissions such as
Create/Read/Update/Delete access, or putting limits on what data the user
can access.

Usage
=====

Using these classes is simple. Simply provide them (or your own class) as a
``Meta`` option to the ``Resource`` in question. For example::

    from django.contrib.auth.models import User
    from tastypie.authorization import DjangoAuthorization
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            authorization = DjangoAuthorization()


Authorization Options
=====================

Tastypie ships with the following ``Authorization`` classes:

``Authorization``
~~~~~~~~~~~~~~~~~

The no-op authorization option, no permissions checks are performed.

.. warning::

  This is a potentially dangerous option, as it means *ANY* recognized user
  can modify *ANY* data they encounter in the API. Be careful who you trust.

``ReadOnlyAuthorization``
~~~~~~~~~~~~~~~~~~~~~~~~~

This authorization class only permits reading data, regardless of what the
``Resource`` might think is allowed. This is the default ``Authorization``
class and the safe option.

``DjangoAuthorization``
~~~~~~~~~~~~~~~~~~~~~~~

The most advanced form of authorization, this checks the permission a user
has granted to them on the resource's model (via ``django.contrib.auth.models.Permission``). In
conjunction with the admin, this is a very effective means of control.

The permissions required using ``DjangoAuthorization`` follow Django Admin's implementation and are as follows:

+---------------------------------+------------------+-----------------------------------------------+----------------------+
| HTTP + URI                      | Method           | User’s permissions required to grant access   | Includes check for   |
+=================================+==================+===============================================+======================+
| ``POST <resource>/``            | create\_list     | ``add``                                       |                      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``POST <resource>/<id>`` (\*)   | create\_detail   | ``add``                                       |                      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``GET <resource>/``             | read\_list       | ``change``                                    |                      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``GET <resouce>/<id>``          | read\_detail     | ``change``                                    |                      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``PUT <resource>/``             | update\_list     | ``change``                                    | ``read_list``        |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``PUT <resource>/<id>``         | update\_detail   | ``change``                                    | ``read_detail``      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``DELETE <resource>/``          | delete\_list     | ``delete``                                    | ``read_list``        |
+---------------------------------+------------------+-----------------------------------------------+----------------------+
| ``DELETE <resource>/``          | delete\_detail   | ``delete``                                    | ``read_detail``      |
+---------------------------------+------------------+-----------------------------------------------+----------------------+

(*) The permission check for ``create_detail`` is implemented in ``DjangoAuthorization``, however ModelResource does not provide an implementation and raises HttpNotImplemented.


Notes:

* The actual permission checked is `<app_label>.<permission>_<model>` where app_label is derived from the resource's model (e.g. `myapp.change_foomodel`)
* `PUT` may revert to `POST` behavior and create new object(s) if the object(s) are not found. In this case the respective `create` permissions are required, instead of the usual `update` permissions.
* Requiring `change` for both read and update is such to keep consistent with Django Admin. To override this behavior and require a custom permission, override DjangoAuthorization as follows::

    class CustomDjangoAuthorization(DjangoAuthorization):
        READ_PERM_CODE = 'view` # matching respective Permission.codename
    
    
The ``Authorization`` API
=========================

An ``Authorization``-compatible class implements the following methods:

* ``read_list``
* ``read_detail``
* ``create_list``
* ``create_detail``
* ``update_list``
* ``update_detail``
* ``delete_list``
* ``delete_detail``

Each method takes two parameters, ``object_list`` & ``bundle``.

``object_list`` is the collection of objects being processed as part of the
request. **FILTERING** & other restrictions to the set will have already been
applied prior to this call.

``bundle`` is the populated ``Bundle`` object for the request. You'll likely
frequently be accessing ``bundle.request.user``, though raw access to the data
can be helpful.

What you return from the method varies based on the type of method.

Return Values: The List Case
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the case of the ``*_list`` methods, you'll want to filter the ``object_list``
& return only the objects the user has access to.

Returning an empty list simply won't allow the action to be applied to any
objects. However, they will not get a HTTP error status code.

If you'd rather they received an unauthorized status code, raising
``Unauthorized`` will return a HTTP ``401``.

Return Values: The Detail Case
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the case of the ``*_detail`` methods, you'll have access to the
``object_list`` (so you know if a given object fits within the overall set),
**BUT** you'll want to be inspecting ``bundle.obj`` & either returning
``True`` if they should be allowed to continue or raising the
``Unauthorized`` exception if not.

Raising ``Unauthorized`` will cause a HTTP ``401`` error status code in the
response.


Implementing Your Own Authorization
===================================

Implementing your own ``Authorization`` classes is a relatively simple
process. Anything that is API-compatible is acceptable, only the method names
matter to Tastypie.

An example implementation of a user only being able to access or modify "their" objects might
look like::

    from tastypie.authorization import Authorization
    from tastypie.exceptions import Unauthorized


    class UserObjectsOnlyAuthorization(Authorization):
        def read_list(self, object_list, bundle):
            # This assumes a ``QuerySet`` from ``ModelResource``.
            return object_list.filter(user=bundle.request.user)

        def read_detail(self, object_list, bundle):
            # Is the requested object owned by the user?
            return bundle.obj.user == bundle.request.user

        def create_list(self, object_list, bundle):
            # Assuming they're auto-assigned to ``user``.
            return object_list

        def create_detail(self, object_list, bundle):
            return bundle.obj.user == bundle.request.user

        def update_list(self, object_list, bundle):
            allowed = []

            # Since they may not all be saved, iterate over them.
            for obj in object_list:
                if obj.user == bundle.request.user:
                    allowed.append(obj)

            return allowed

        def update_detail(self, object_list, bundle):
            return bundle.obj.user == bundle.request.user

        def delete_list(self, object_list, bundle):
            # Sorry user, no deletes for you!
            raise Unauthorized("Sorry, no deletes.")

        def delete_detail(self, object_list, bundle):
            raise Unauthorized("Sorry, no deletes.")
