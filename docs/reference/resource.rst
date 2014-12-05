.. _resource-reference:

Resource Reference
******************

In terms of a REST-style architecture, a "resource" is a collection of similar
data. This data could be a table of a database, a collection of other resources
or a similar form of data storage. In Tastypie, these resources are generally
intermediaries between the end user & objects, usually Django models. As such,
``Resource`` (and its model-specific twin ``ModelResource``) form the heart of
Tastypie's functionality.

::

    from tastypie.resources import ModelResource
    from my_app.models import MyModel, get_my_model_statistics()


    class MyModelResource(ModelResource):
        # Fields, ModelResource includes fields from the Model it matches
        user = fields.ForeignKey(UserResource, 'user')
    
        # Options, inside the Meta class
        class Meta:
            queryset = MyModel.objects.all()
            allowed_methods = ['get']

        # Methods
        def dehydrate(self, bundle):
            bundle.data['custom_field'] = "Whatever you want"
            return bundle


Resource Options (AKA ``Meta``)
===============================

The inner ``Meta`` class allows for class-level configuration of how the
``Resource`` should behave. The following options are available:


``serializer``
--------------

.. attribute:: Resource.serializer

  Controls which serializer class the ``Resource`` should use. Default is
  ``tastypie.serializers.Serializer()``.


``authentication``
------------------

.. attribute:: Resource.authentication

  Controls which authentication class the ``Resource`` should use. Default is
  ``tastypie.authentication.Authentication()``.


``authorization``
-----------------

  Controls which authorization class the ``Resource`` should use. Default is
  ``tastypie.authorization.ReadOnlyAuthorization()``.


``validation``
--------------

  Controls which validation class the ``Resource`` should use. Default is
  ``tastypie.validation.Validation()``.


``paginator_class``
-------------------

  Controls which paginator class the ``Resource`` should use. Default is
  ``tastypie.paginator.Paginator``.

.. note::

  This is different than the other options in that you supply a class rather
  than an instance. This is done because the Paginator has some per-request
  initialization options.


``cache``
---------

  Controls which cache class the ``Resource`` should use. Default is
  ``tastypie.cache.NoCache()``.


``throttle``
------------

  Controls which throttle class the ``Resource`` should use. Default is
  ``tastypie.throttle.BaseThrottle()``.


``allowed_methods``
-------------------

  Controls what list & detail REST methods the ``Resource`` should respond to.
  Default is ``None``, which means delegate to the more specific
  ``list_allowed_methods`` & ``detail_allowed_methods`` options.

  You may specify a list like ``['get', 'post', 'put', 'delete', 'patch']`` as a shortcut
  to prevent having to specify the other options.


``list_allowed_methods``
------------------------

  Controls what list REST methods the ``Resource`` should respond to. Default
  is ``['get', 'post', 'put', 'delete', 'patch']``.


.. _detail-allowed-methods:

``detail_allowed_methods``
--------------------------

  Controls what detail REST methods the ``Resource`` should respond to. Default
  is ``['get', 'post', 'put', 'delete', 'patch']``.


``limit``
---------

  Controls how many results the ``Resource`` will show at a time. Default
  is either the ``API_LIMIT_PER_PAGE`` setting (if provided) or ``20`` if not
  specified.


``max_limit``
-------------

  Controls the maximum number of results the ``Resource`` will show at a time.
  If the user-specified ``limit`` is higher than this, it will be capped to
  this limit. Set to ``0`` or ``None`` to allow unlimited results.


``api_name``
------------

  An override for the ``Resource`` to use when generating resource URLs.
  Default is ``None``.


``resource_name``
-----------------

  An override for the ``Resource`` to use when generating resource URLs.
  Default is ``None``.

  If not provided, the ``Resource`` or ``ModelResource`` will attempt to name
  itself. This means a lowercase version of the classname preceding the word
  ``Resource`` if present (i.e. ``SampleContentResource`` would become
  ``samplecontent``).


``default_format``
------------------

  Specifies the default serialization format the ``Resource`` should use if
  one is not requested (usually by the ``Accept`` header or ``format`` GET
  parameter). Default is ``application/json``.


``filtering``
-------------

  Provides a list of fields that the ``Resource`` will accept client
  filtering on. Default is ``{}``.

  Keys should be the fieldnames as strings while values should be a list of
  accepted filter types.


``ordering``
------------

  Specifies the what fields the ``Resource`` should should allow ordering on.
  Default is ``[]``.

  Values should be the fieldnames as strings. When provided to the ``Resource``
  by the ``order_by`` GET parameter, you can specify either the ``fieldname``
  (ascending order) or ``-fieldname`` (descending order).


``object_class``
----------------

  Provides the ``Resource`` with the object that serves as the data source.
  Default is ``None``.

  In the case of ``ModelResource``, this is automatically populated by the
  ``queryset`` option and is the model class.


``queryset``
------------

  Provides the ``Resource`` with the set of Django models to respond with.
  Default is ``None``.

  Unused by ``Resource`` but present for consistency.

.. warning::

  If you place any callables in this, they'll only be evaluated once (when
  the ``Meta`` class is instantiated). This especially affects things that
  are date/time related. Please see the :ref:`Tastypie Cookbook <ref-cookbook>`
  for a way around this.


``fields``
----------

  Controls what introspected fields the ``Resource`` should include.
  A whitelist of fields. Default is ``[]``.


``excludes``
------------

  Controls what introspected fields the ``Resource`` should *NOT* include.
  A blacklist of fields. Default is ``[]``.

``include_resource_uri``
------------------------

  Specifies if the ``Resource`` should include an extra field that displays
  the detail URL (within the api) for that resource. Default is ``True``.

``include_absolute_url``
------------------------

  Specifies if the ``Resource`` should include an extra field that displays
  the ``get_absolute_url`` for that object (on the site proper). Default is
  ``False``.

``always_return_data``
------------------------

  Specifies all HTTP methods (except ``DELETE``) should return a serialized form
  of the data. Default is ``False``.

  If ``False``, ``HttpNoContent`` (204) is returned on ``POST/PUT``
  with an empty body & a ``Location`` header of where to request the full
  resource.

  If ``True``, ``HttpAccepted`` (202) is returned on ``POST/PUT``
  with a body containing all the data in a serialized form.

``collection_name``
-------------------

  Specifies the collection of objects returned in the ``GET`` list will be
  named. Default is ``objects``.

``detail_uri_name``
-------------------

  Specifies the name for the regex group that matches on detail views. Defaults
  to ``pk``.


``Resource`` Methods
====================

Handles the data, request dispatch and responding to requests.

Serialization/deserialization is handled "at the edges" (i.e. at the
beginning/end of the request/response cycle) so that everything internally
is Python data structures.

This class tries to be non-model specific, so it can be hooked up to other
data sources, such as search results, files, other data, etc.

``wrap_view``
-------------

.. method:: Resource.wrap_view(self, view)

Wraps methods so they can be called in a more functional way as well
as handling exceptions better.

Note that if ``BadRequest`` or an exception with a ``response`` attr are seen,
there is special handling to either present a message back to the user or
return the response traveling with the exception.

``base_urls``
-------------

.. method:: Resource.base_urls(self)

The standard URLs this ``Resource`` should respond to. These include the
list, detail, schema & multiple endpoints by default.

Should return a list of individual URLconf lines (**NOT** wrapped in
``patterns``).

``override_urls``
-----------------

.. method:: Resource.override_urls(self)

Deprecated. Will be removed by v1.0.0. Please use ``Resource.prepend_urls``
instead.

``prepend_urls``
----------------

.. method:: Resource.prepend_urls(self)

A hook for adding your own URLs or matching before the default URLs. Useful for
adding custom endpoints or overriding the built-in ones (from ``base_urls``).

Should return a list of individual URLconf lines (**NOT** wrapped in
``patterns``).

``urls``
--------

.. method:: Resource.urls(self)

*Property*

The endpoints this ``Resource`` responds to. A combination of ``base_urls`` &
``override_urls``.

Mostly a standard URLconf, this is suitable for either automatic use
when registered with an ``Api`` class or for including directly in
a URLconf should you choose to.

``determine_format``
--------------------

.. method:: Resource.determine_format(self, request)

Used to determine the desired format.

Largely relies on ``tastypie.utils.mime.determine_format`` but here
as a point of extension.

``serialize``
-------------

.. method:: Resource.serialize(self, request, data, format, options=None)

Given a request, data and a desired format, produces a serialized
version suitable for transfer over the wire.

Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.

``deserialize``
---------------

.. method:: Resource.deserialize(self, request, data, format='application/json')

Given a request, data and a format, deserializes the given data.

It relies on the request properly sending a ``CONTENT_TYPE`` header,
falling back to ``application/json`` if not provided.

Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.

``alter_list_data_to_serialize``
--------------------------------

.. method:: Resource.alter_list_data_to_serialize(self, request, data)

A hook to alter list data just before it gets serialized & sent to the user.

Useful for restructuring/renaming aspects of the what's going to be
sent.

Should accommodate for a list of objects, generally also including
meta data.

``alter_detail_data_to_serialize``
----------------------------------

.. method:: Resource.alter_detail_data_to_serialize(self, request, data)

A hook to alter detail data just before it gets serialized & sent to the user.

Useful for restructuring/renaming aspects of the what's going to be
sent.

Should accommodate for receiving a single bundle of data.

``alter_deserialized_list_data``
--------------------------------

.. method:: Resource.alter_deserialized_list_data(self, request, data)

A hook to alter list data just after it has been received from the user &
gets deserialized.

Useful for altering the user data before any hydration is applied.

``alter_deserialized_detail_data``
----------------------------------

.. method:: Resource.alter_deserialized_detail_data(self, request, data)

A hook to alter detail data just after it has been received from the user &
gets deserialized.

Useful for altering the user data before any hydration is applied.

``dispatch_list``
-----------------

.. method:: Resource.dispatch_list(self, request, **kwargs)

A view for handling the various HTTP methods (GET/POST/PUT/DELETE) over
the entire list of resources.

Relies on ``Resource.dispatch`` for the heavy-lifting.

``dispatch_detail``
-------------------

.. method:: Resource.dispatch_detail(self, request, **kwargs)

A view for handling the various HTTP methods (GET/POST/PUT/DELETE) on
a single resource.

Relies on ``Resource.dispatch`` for the heavy-lifting.

``dispatch``
------------

.. method:: Resource.dispatch(self, request_type, request, **kwargs)

Handles the common operations (allowed HTTP method, authentication,
throttling, method lookup) surrounding most CRUD interactions.

``remove_api_resource_names``
-----------------------------

.. method:: Resource.remove_api_resource_names(self, url_dict)

Given a dictionary of regex matches from a URLconf, removes
``api_name`` and/or ``resource_name`` if found.

This is useful for converting URLconf matches into something suitable
for data lookup. For example::

    Model.objects.filter(**self.remove_api_resource_names(matches))

``method_check``
----------------

.. method:: Resource.method_check(self, request, allowed=None)

Ensures that the HTTP method used on the request is allowed to be
handled by the resource.

Takes an ``allowed`` parameter, which should be a list of lowercase
HTTP methods to check against. Usually, this looks like::

    # The most generic lookup.
    self.method_check(request, self._meta.allowed_methods)

    # A lookup against what's allowed for list-type methods.
    self.method_check(request, self._meta.list_allowed_methods)

    # A useful check when creating a new endpoint that only handles
    # GET.
    self.method_check(request, ['get'])

``is_authorized``
-----------------

.. method:: Resource.is_authorized(self, request, object=None)

Handles checking of permissions to see if the user has authorization
to GET, POST, PUT, or DELETE this resource.  If ``object`` is provided,
the authorization backend can apply additional row-level permissions
checking.

``is_authenticated``
--------------------

.. method:: Resource.is_authenticated(self, request)

Handles checking if the user is authenticated and dealing with
unauthenticated users.

Mostly a hook, this uses class assigned to ``authentication`` from
``Resource._meta``.

``throttle_check``
------------------

.. method:: Resource.throttle_check(self, request)

Handles checking if the user should be throttled.

Mostly a hook, this uses class assigned to ``throttle`` from
``Resource._meta``.

``log_throttled_access``
------------------------

.. method:: Resource.log_throttled_access(self, request)

Handles the recording of the user's access for throttling purposes.

Mostly a hook, this uses class assigned to ``throttle`` from
``Resource._meta``.

``build_bundle``
----------------

.. method:: Resource.build_bundle(self, obj=None, data=None, request=None)

Given either an object, a data dictionary or both, builds a ``Bundle``
for use throughout the ``dehydrate/hydrate`` cycle.

If no object is provided, an empty object from
``Resource._meta.object_class`` is created so that attempts to access
``bundle.obj`` do not fail.

``build_filters``
-----------------

.. method:: Resource.build_filters(self, filters=None)

Allows for the filtering of applicable objects.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``apply_sorting``
-----------------

.. method:: Resource.apply_sorting(self, obj_list, options=None)

Allows for the sorting of objects being returned.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``get_bundle_detail_data``
--------------------------

.. method:: Resource.get_bundle_detail_data(self, bundle)

Convenience method to return the ``detail_uri_name`` attribute off
``bundle.obj``.

Usually just accesses ``bundle.obj.pk`` by default.

``get_resource_uri``
--------------------

.. method:: Resource.get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list')

Handles generating a resource URI.

If the ``bundle_or_obj`` argument is not provided, it builds the URI
for the list endpoint.

If the ``bundle_or_obj`` argument is provided, it builds the URI for
the detail endpoint.

Return the generated URI. If that URI can not be reversed (not found
in the URLconf), it will return an empty string.

``resource_uri_kwargs``
-----------------------

.. method:: Resource.resource_uri_kwargs(self, bundle_or_obj=None)

Handles generating a resource URI.

If the ``bundle_or_obj`` argument is not provided, it builds the URI
for the list endpoint.

If the ``bundle_or_obj`` argument is provided, it builds the URI for
the detail endpoint.

Return the generated URI. If that URI can not be reversed (not found
in the URLconf), it will return ``None``.

``detail_uri_kwargs``
---------------------

.. method:: Resource.detail_uri_kwargs(self, bundle_or_obj)

This needs to be implemented at the user level.

Given a ``Bundle`` or an object, it returns the extra kwargs needed to
generate a detail URI.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``get_via_uri``
---------------

.. method:: Resource.get_via_uri(self, uri, request=None)

This pulls apart the salient bits of the URI and populates the
resource via a ``obj_get``.

Optionally accepts a ``request``.

If you need custom behavior based on other portions of the URI,
simply override this method.

``full_dehydrate``
------------------

.. method:: Resource.full_dehydrate(self, bundle, for_list=False)

Given a bundle with an object instance, extract the information from it to
populate the resource.

The for_list flag is used to control which fields are excluded by the ``use_in`` attribute.

``dehydrate``
-------------

.. method:: Resource.dehydrate(self, bundle)

A hook to allow a final manipulation of data once all fields/methods
have built out the dehydrated data.

Useful if you need to access more than one dehydrated field or want
to annotate on additional data.

Must return the modified bundle.

``full_hydrate``
----------------

.. method:: Resource.full_hydrate(self, bundle)

Given a populated bundle, distill it and turn it back into
a full-fledged object instance.

``hydrate``
-----------

.. method:: Resource.hydrate(self, bundle)

A hook to allow a final manipulation of data once all fields/methods
have built out the hydrated data.

Useful if you need to access more than one hydrated field or want
to annotate on additional data.

Must return the modified bundle.

``hydrate_m2m``
---------------

.. method:: Resource.hydrate_m2m(self, bundle)

Populate the ManyToMany data on the instance.

``build_schema``
----------------

.. method:: Resource.build_schema(self)

Returns a dictionary of all the fields on the resource and some
properties about those fields.

Used by the ``schema/`` endpoint to describe what will be available.

``dehydrate_resource_uri``
--------------------------

.. method:: Resource.dehydrate_resource_uri(self, bundle)

For the automatically included ``resource_uri`` field, dehydrate
the URI for the given bundle.

Returns empty string if no URI can be generated.

``generate_cache_key``
----------------------

.. method:: Resource.generate_cache_key(self, *args, **kwargs)

Creates a unique-enough cache key.

This is based off the current api_name/resource_name/args/kwargs.

``get_object_list``
-------------------

.. method:: Resource.get_object_list(self, request)

A hook to allow making returning the list of available objects.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``apply_authorization_limits``
------------------------------

.. method:: Resource.apply_authorization_limits(self, request, object_list)

Allows the ``Authorization`` class to further limit the object list.
Also a hook to customize per ``Resource``.

Calls ``Authorization.apply_limits`` if available.

``can_create``
--------------

.. method:: Resource.can_create(self)

Checks to ensure ``post`` is within ``allowed_methods``.

``can_update``
--------------

.. method:: Resource.can_update(self)

Checks to ensure ``put`` is within ``allowed_methods``.

Used when hydrating related data.

``can_delete``
--------------

.. method:: Resource.can_delete(self)

Checks to ensure ``delete`` is within ``allowed_methods``.

``apply_filters``
-----------------

.. method:: Resource.apply_filters(self, request, applicable_filters)

A hook to alter how the filters are applied to the object list.

This needs to be implemented at the user level.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_get_list``
----------------

.. method:: Resource.obj_get_list(self, bundle, **kwargs)

Fetches the list of objects available on the resource.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``cached_obj_get_list``
-----------------------

.. method:: Resource.cached_obj_get_list(self, bundle, **kwargs)

A version of ``obj_get_list`` that uses the cache as a means to get
commonly-accessed data faster.

``obj_get``
-----------

.. method:: Resource.obj_get(self, bundle, **kwargs)

Fetches an individual object on the resource.

*This needs to be implemented at the user level.* If the object can not
be found, this should raise a ``NotFound`` exception.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``cached_obj_get``
------------------

.. method:: Resource.cached_obj_get(self, bundle, **kwargs)

A version of ``obj_get`` that uses the cache as a means to get
commonly-accessed data faster.

``obj_create``
--------------

.. method:: Resource.obj_create(self, bundle, **kwargs)

Creates a new object based on the provided data.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``lookup_kwargs_with_identifiers``
----------------------------------

.. method:: Resource.lookup_kwargs_with_identifiers(self, bundle, kwargs)

Kwargs here represent uri identifiers. Ex: /repos/<user_id>/<repo_name>/
We need to turn those identifiers into Python objects for generating
lookup parameters that can find them in the DB.

``obj_update``
--------------

.. method:: Resource.obj_update(self, bundle, **kwargs)

Updates an existing object (or creates a new object) based on the
provided data.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_delete_list``
-------------------

.. method:: Resource.obj_delete_list(self, bundle, **kwargs)

Deletes an entire list of objects.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_delete_list_for_update``
------------------------------

.. method:: Resource.obj_delete_list_for_update(self, bundle, **kwargs)

Deletes an entire list of objects, specific to PUT list.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_delete``
--------------

.. method:: Resource.obj_delete(self, bundle, **kwargs)

Deletes a single object.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``create_response``
-------------------

.. method:: Resource.create_response(self, request, data, response_class=HttpResponse, **response_kwargs)

Extracts the common "which-format/serialize/return-response" cycle.

Mostly a useful shortcut/hook.

``is_valid``
------------

.. method:: Resource.is_valid(self, bundle)

Handles checking if the data provided by the user is valid.

Mostly a hook, this uses class assigned to ``validation`` from
``Resource._meta``.

If validation fails, an error is raised with the error messages
serialized inside it.

``rollback``
------------

.. method:: Resource.rollback(self, bundles)

Given the list of bundles, delete all objects pertaining to those
bundles.

This needs to be implemented at the user level. No exceptions should
be raised if possible.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``get_list``
------------

.. method:: Resource.get_list(self, request, **kwargs)

Returns a serialized list of resources.

Calls ``obj_get_list`` to provide the data, then handles that result
set and serializes it.

Should return a HttpResponse (200 OK).

``get_detail``
--------------

.. method:: Resource.get_detail(self, request, **kwargs)

Returns a single serialized resource.

Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
set and serializes it.

Should return a HttpResponse (200 OK).

``put_list``
------------

.. method:: Resource.put_list(self, request, **kwargs)

Replaces a collection of resources with another collection.

Calls ``delete_list`` to clear out the collection then ``obj_create``
with the provided the data to create the new collection.

Return ``HttpNoContent`` (204 No Content) if
``Meta.always_return_data = False`` (default).

Return ``HttpAccepted`` (202 Accepted) if
``Meta.always_return_data = True``.

``put_detail``
--------------

.. method:: Resource.put_detail(self, request, **kwargs)

Either updates an existing resource or creates a new one with the
provided data.

Calls ``obj_update`` with the provided data first, but falls back to
``obj_create`` if the object does not already exist.

If a new resource is created, return ``HttpCreated`` (201 Created).
If ``Meta.always_return_data = True``, there will be a populated body
of serialized data.

If an existing resource is modified and
``Meta.always_return_data = False`` (default), return ``HttpNoContent``
(204 No Content).
If an existing resource is modified and
``Meta.always_return_data = True``, return ``HttpAccepted`` (202
Accepted).

``post_list``
-------------

.. method:: Resource.post_list(self, request, **kwargs)

Creates a new resource/object with the provided data.

Calls ``obj_create`` with the provided data and returns a response
with the new resource's location.

If a new resource is created, return ``HttpCreated`` (201 Created).
If ``Meta.always_return_data = True``, there will be a populated body
of serialized data.

``post_detail``
---------------

.. method:: Resource.post_detail(self, request, **kwargs)

Creates a new subcollection of the resource under a resource.

This is not implemented by default because most people's data models
aren't self-referential.

If a new resource is created, return ``HttpCreated`` (201 Created).

``delete_list``
---------------

.. method:: Resource.delete_list(self, request, **kwargs)

Destroys a collection of resources/objects.

Calls ``obj_delete_list``.

If the resources are deleted, return ``HttpNoContent`` (204 No Content).

``delete_detail``
-----------------

.. method:: Resource.delete_detail(self, request, **kwargs)

Destroys a single resource/object.

Calls ``obj_delete``.

If the resource is deleted, return ``HttpNoContent`` (204 No Content).
If the resource did not exist, return ``HttpNotFound`` (404 Not Found).


.. _patch-list:

``patch_list``
--------------

.. method:: Resource.patch_list(self, request, **kwargs)

Updates a collection in-place.

The exact behavior of ``PATCH`` to a list resource is still the matter of
some debate in REST circles, and the ``PATCH`` RFC isn't standard. So the
behavior this method implements (described below) is something of a
stab in the dark. It's mostly cribbed from GData, with a smattering
of ActiveResource-isms and maybe even an original idea or two.

The ``PATCH`` format is one that's similar to the response returned from
a ``GET`` on a list resource::

    {
      "objects": [{object}, {object}, ...],
      "deleted_objects": ["URI", "URI", "URI", ...],
    }

For each object in ``objects``:

  * If the dict does not have a ``resource_uri`` key then the item is
    considered "new" and is handled like a ``POST`` to the resource list.

  * If the dict has a ``resource_uri`` key and the ``resource_uri`` refers
    to an existing resource then the item is a update; it's treated
    like a ``PATCH`` to the corresponding resource detail.

  * If the dict has a ``resource_uri`` but the resource *doesn't* exist,
    then this is considered to be a create-via-``PUT``.

Each entry in ``deleted_objects`` referes to a resource URI of an existing
resource to be deleted; each is handled like a ``DELETE`` to the relevent
resource.

In any case:

  * If there's a resource URI it *must* refer to a resource of this
    type. It's an error to include a URI of a different resource.

  * ``PATCH`` is all or nothing. If a single sub-operation fails, the
    entire request will fail and all resources will be rolled back.

  * For ``PATCH`` to work, you **must** have ``put`` in your
    :ref:`detail-allowed-methods` setting.

  * To delete objects via ``deleted_objects`` in a ``PATCH`` request you
    **must** have ``delete`` in your :ref:`detail-allowed-methods` setting.


``patch_detail``
----------------

.. method:: Resource.patch_detail(self, request, **kwargs)

Updates a resource in-place.

Calls ``obj_update``.

If the resource is updated, return ``HttpAccepted`` (202 Accepted).
If the resource did not exist, return ``HttpNotFound`` (404 Not Found).

``get_schema``
--------------

.. method:: Resource.get_schema(self, request, **kwargs)

Returns a serialized form of the schema of the resource.

Calls ``build_schema`` to generate the data. This method only responds
to HTTP GET.

Should return a HttpResponse (200 OK).

``get_multiple``
----------------

.. method:: Resource.get_multiple(self, request, **kwargs)

Returns a serialized list of resources based on the identifiers
from the URL.

Calls ``obj_get`` to fetch only the objects requested. This method
only responds to HTTP GET.

Should return a HttpResponse (200 OK).


See Also
========

See also :ref:`ModelResource reference <model-resource-reference>`.

