.. _ref-resources:

=========
Resources
=========

In terms of a REST-style architecture, a "resource" is a collection of similar
data. This data could be a table of a database, a collection of other resources
or a similar form of data storage. In Tastypie, these resources are generally
intermediaries between the end user & objects, usually Django models. As such,
``Resource`` (and its model-specific twin ``ModelResource``) form the heart of
Tastypie's functionality.


Quick Start
===========

A sample resource definition might look something like::

    from django.contrib.auth.models import User
    from tastypie import fields
    from tastypie.authorization import DjangoAuthorization
    from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
    from myapp.models import Entry
    
    
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
    
    
    class EntryResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user')
        
        class Meta:
            queryset = Entry.objects.all()
            list_allowed_methods = ['get', 'post']
            detail_allowed_methods = ['get', 'post', 'put', 'delete']
            resource_name = 'myapp/entry'
            authorization = DjangoAuthorization()
            filtering = {
                'slug': ALL,
                'user': ALL_WITH_RELATIONS,
                'created': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            }


Why Class-Based?
================

Using class-based resources make it easier to extend/modify the code to meet
your needs. APIs are rarely a one-size-fits-all problem space, so Tastypie
tries to get the fundamentals right and provide you with enough hooks to
customize things to work your way.

As is standard, this raises potential problems for thread-safety. Tastypie has
been designed to minimize the possibility of data "leaking" between threads.
This does however sometimes introduce some small complexities & you should be
careful not to store state on the instances if you're going to be using the
code in a threaded environment.


Why ``Resource`` vs. ``ModelResource``?
=======================================

Make no mistake that Django models are far and away the most popular source of
data. However, in practice, there are many times where the ORM isn't the data
source. Hooking up things like a NoSQL store, a search solution like Haystack
or even managed filesystem data are all good use cases for ``Resource`` knowing
nothing about the ORM.


Flow Through The Request/Response Cycle
=======================================

TBD


What Are Bundles?
=================

Bundles are a small abstraction that allow Tastypie to pass data between
resources. This allows us not to depend on passing ``request`` to every single
method (especially in places where this would be overkill). It also allows
resources to work with data coming into the application paired together with
an unsaved instance of the object in question.

Think of it as package of user data & an object instance (either of which are
optionally present).


Why Resource URIs?
==================

Resource URIs play a heavy role in how Tastypie delivers data. This can seem
very different from other solutions which simply inline related data. Though
Tastypie can inline data like that (using ``full=True`` on the field with the
relation), the default is to provide URIs.

URIs are useful because it results in smaller payloads, letting you fetch only
the data that is important to you. You can imagine an instance where an object
has thousands of related items that you may not be interested in.

URIs are also very cache-able, because the data at each endpoint is less likely
to frequently change.

And URIs encourage proper use of each endpoint to display the data that endpoint
covers.

Ideology aside, you should use whatever suits you. If you prefer fewer requests
& fewer endpoints, use of ``full=True`` is available, but be aware of the
consequences of each approach.


Advanced Data Preparation
=========================

Tastypie uses a "dehydrate" cycle to prepare data for serialization & a
"hydrate" cycle to take data sent to it & turn that back into useful Python
objects.

Within these cycles, there are several points of customization if you need them.

``dehydrate``
-------------

``dehydrate_FOO``
-----------------

``hydrate``
-----------

``hydrate_FOO``
---------------


Reverse "Relationships"
=======================

Unlike Django's ORM, Tastypie does not automatically create reverse relations.
This is because there is substantial technical complexity involved, as well as
perhaps unintentionally exposing related data in an incorrect way to the end
user of the API.

However, it is still possible to create reverse relations. Instead of handing
the ``ToOneField`` or ``ToManyField`` a class, pass them a string that
represents the full path to the desired class. Implementing a reverse
relationship looks like so::

  # myapp/api/resources.py
  from tastypie import fields
  from tastypie.resources import ModelResource
  from myapp.models import Note, Comment
  
  
  class NoteResource(ModelResource):
      comments = fields.ToManyField('myapp.api.resources.CommentResource', 'comments')
      
      class Meta:
          queryset = Note.objects.all()
  
  
  class CommentResource(ModelResource):
      note = fields.ToOneField(NoteResource, 'notes')
      
      class Meta:
          queryset = Comment.objects.all()

.. warning::

  Unlike Django, you can't use just the class name (i.e. ``'CommentResource'``),
  even if it's in the same module. Tastypie (intentionally) lacks a construct
  like the ``AppCache`` which makes that sort of thing work in Django. Sorry.

Tastypie also supports self-referential relations. If you assume we added the
appropriate self-referential ``ForeignKey`` to the ``Note`` model, implementing
a similar relation in Tastypie would look like::

  # myapp/api/resources.py
  from tastypie import fields
  from tastypie.resources import ModelResource
  from myapp.models import Note
  
  
  class NoteResource(ModelResource):
      sub_notes = fields.ToManyField('self', 'notes')
      
      class Meta:
          queryset = Note.objects.all()


Resource Options (AKA ``Meta``)
===============================

The inner ``Meta`` class allows for class-level configuration of how the
``Resource`` should behave. The following options are available:

``serializer``
--------------

  Controls which serializer class the ``Resource`` should use. Default is
  ``tastypie.serializers.Serializer()``.

``authentication``
------------------

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
  
  You may specify a list like ``['get', 'post', 'put', 'delete']`` as a shortcut
  to prevent having to specify the other options.

``list_allowed_methods``
------------------------

  Controls what list REST methods the ``Resource`` should respond to. Default
  is ``['get', 'post', 'put', 'delete']``.

``detail_allowed_methods``
--------------------------

  Controls what list REST methods the ``Resource`` should respond to. Default
  is ``['get', 'post', 'put', 'delete']``.

``limit``
---------

  Controls what how many results the ``Resource`` will show at a time. Default
  is either the ``API_LIMIT_PER_PAGE`` setting (if provided) or ``20`` if not
  specified.

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


Basic Filtering
===============

:class:`~tastypie.resources.ModelResource` provides a basic Django ORM filter
interface. Simply list the resource fields which you'd like to filter on and
the allowed expression in a `filtering` property of your resource's Meta
class::

    from tastypie.constants import ALL, ALL_WITH_RELATIONS

    class MyResource(ModelResource):
        class Meta:
            filtering = {
                "slug": ('exact', 'startswith',),
                "title": ALL,
            }

Valid filtering values are: Django ORM filters (e.g. ``startswith``,
``exact``, ``lte``, etc. or the ``ALL`` or ``ALL_WITH_RELATIONS`` constants
defined in :mod:`tastypie.constants`.

These filters will be extracted from URL query strings using the same
double-underscore syntax as the Django ORM::

    /api/v1/myresource/?slug=myslug
    /api/v1/myresource/?slug__startswith=test


Advanced Filtering
==================

If you need to filter things other than ORM resources or wish to apply
additional constraints (e.g. text filtering using `django-haystack
<http://haystacksearch.org>` rather than simple database queries) your
:class:`~tastypie.resources.Resource` may define a custom
:meth:`~tastypie.resource.Resource.build_filters` method which allows you to
filter the queryset before processing a request::

    from haystack.query import SearchQuerySet
    
    class MyResource(Resource):
        def build_filters(self, filters=None):
            if filters is None:
                filters = {}
            
            orm_filters = super(MyResource, self).build_filters(filters)
            
            if "q" in filters:
                sqs = SearchQuerySet().auto_query(filters['q'])
                
                orm_filters = {"pk__in": [ i.pk for i in sqs ]}
            
            return orm_filters


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

A hook for adding your own URLs or overriding the default URLs. Useful for
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

.. method:: Resource.build_bundle(self, obj=None, data=None)

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

``get_resource_uri``
--------------------

.. method:: Resource.get_resource_uri(self, bundle_or_obj)

*This needs to be implemented at the user level.*

A ``return reverse("api_dispatch_detail", kwargs={'resource_name':
self.resource_name, 'pk': object.id})`` should be all that would
be needed.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``get_resource_list_uri``
-------------------------

.. method:: Resource.get_resource_list_uri(self)

Returns a URL specific to this resource's list endpoint.

``get_via_uri``
---------------

.. method:: Resource.get_via_uri(self, uri)

This pulls apart the salient bits of the URI and populates the
resource via a ``obj_get``.

If you need custom behavior based on other portions of the URI,
simply override this method.

``full_dehydrate``
------------------

.. method:: Resource.full_dehydrate(self, obj)

Given an object instance, extract the information from it to populate
the resource.

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

``obj_get_list``
----------------

.. method:: Resource.obj_get_list(self, request=None, **kwargs)

Fetches the list of objects available on the resource.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``cached_obj_get_list``
-----------------------

.. method:: Resource.cached_obj_get_list(self, request=None, **kwargs)

A version of ``obj_get_list`` that uses the cache as a means to get
commonly-accessed data faster.

``obj_get``
-----------

.. method:: Resource.obj_get(self, request=None, **kwargs)

Fetches an individual object on the resource.

*This needs to be implemented at the user level.* If the object can not
be found, this should raise a ``NotFound`` exception.

``ModelResource`` includes a full working version specific to Django's
``Models``.

``cached_obj_get``
------------------

.. method:: Resource.cached_obj_get(self, request=None, **kwargs)

A version of ``obj_get`` that uses the cache as a means to get
commonly-accessed data faster.

``obj_create``
--------------

.. method:: Resource.obj_create(self, bundle, request=None, **kwargs)

Creates a new object based on the provided data.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_update``
--------------

.. method:: Resource.obj_update(self, bundle, request=None, **kwargs)

Updates an existing object (or creates a new object) based on the
provided data.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_delete_list``
-------------------

.. method:: Resource.obj_delete_list(self, request=None, **kwargs)

Deletes an entire list of objects.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``obj_delete``
--------------

.. method:: Resource.obj_delete(self, request=None, **kwargs)

Deletes a single object.

*This needs to be implemented at the user level.*

``ModelResource`` includes a full working version specific to Django's
``Models``.

``create_response``
-------------------

.. method:: Resource.create_response(self, request, data)

Extracts the common "which-format/serialize/return-response" cycle.

Mostly a useful shortcut/hook.

``is_valid``
------------

.. method:: Resource.is_valid(self, bundle, request=None)

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

Return ``HttpAccepted`` (204 No Content).

``put_detail``
--------------

.. method:: Resource.put_detail(self, request, **kwargs)

Either updates an existing resource or creates a new one with the
provided data.

Calls ``obj_update`` with the provided data first, but falls back to
``obj_create`` if the object does not already exist.

If a new resource is created, return ``HttpCreated`` (201 Created).
If an existing resource is modified, return ``HttpAccepted`` (204 No Content).

``post_list``
-------------

.. method:: Resource.post_list(self, request, **kwargs)

Creates a new resource/object with the provided data.

Calls ``obj_create`` with the provided data and returns a response
with the new resource's location.

If a new resource is created, return ``HttpCreated`` (201 Created).

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

If the resources are deleted, return ``HttpAccepted`` (204 No Content).

``delete_detail``
-----------------

.. method:: Resource.delete_detail(self, request, **kwargs)

Destroys a single resource/object.

Calls ``obj_delete``.

If the resource is deleted, return ``HttpAccepted`` (204 No Content).
If the resource did not exist, return ``HttpGone`` (410 Gone).

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


``ModelResource`` Methods
=========================

A subclass of ``Resource`` designed to work with Django's ``Models``.

This class will introspect a given ``Model`` and build a field list based
on the fields found on the model (excluding relational fields).

Given that it is aware of Django's ORM, it also handles the CRUD data
operations of the resource.

``should_skip_field``
---------------------

.. method:: ModelResource.should_skip_field(cls, field)

*Class method*

Given a Django model field, return if it should be included in the
contributed ApiFields.

``api_field_from_django_field``
-------------------------------

.. method:: ModelResource.api_field_from_django_field(cls, f, default=CharField)

*Class method*

Returns the field type that would likely be associated with each
Django type.

``get_fields``
--------------

.. method:: ModelResource.get_fields(cls, fields=None, excludes=None)

*Class method*

Given any explicit fields to include and fields to exclude, add
additional fields based on the associated model.

``build_filters``
-----------------

.. method:: ModelResource.build_filters(self, filters=None)

Given a dictionary of filters, create the necessary ORM-level filters.

Keys should be resource fields, **NOT** model fields.

Valid values are either a list of Django filter types (i.e.
``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
``ALL_WITH_RELATIONS`` constant.

At the declarative level::

    filtering = {
        'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        'resource_field_name_3': ALL,
        'resource_field_name_4': ALL_WITH_RELATIONS,
        ...
    }

Accepts the filters as a dict. ``None`` by default, meaning no filters.

``apply_sorting``
-----------------

.. method:: ModelResource.apply_sorting(self, obj_list, options=None)

Given a dictionary of options, apply some ORM-level sorting to the
provided ``QuerySet``.

Looks for the ``order_by`` key and handles either ascending (just the
field name) or descending (the field name with a ``-`` in front).

The field name should be the resource field, **NOT** model field.

``get_object_list``
-------------------

.. method:: ModelResource.get_object_list(self, request)

A ORM-specific implementation of ``get_object_list``.

Returns a ``QuerySet`` that may have been limited by authorization or other
overrides.

``obj_get_list``
----------------

.. method:: ModelResource.obj_get_list(self, filters=None, **kwargs)

A ORM-specific implementation of ``obj_get_list``.

Takes an optional ``filters`` dictionary, which can be used to narrow
the query.

``obj_get``
-----------

.. method:: ModelResource.obj_get(self, **kwargs)

A ORM-specific implementation of ``obj_get``.

Takes optional ``kwargs``, which are used to narrow the query to find
the instance.

``obj_create``
--------------

.. method:: ModelResource.obj_create(self, bundle, **kwargs)

A ORM-specific implementation of ``obj_create``.

``obj_update``
--------------

.. method:: ModelResource.obj_update(self, bundle, **kwargs)

A ORM-specific implementation of ``obj_update``.

``obj_delete_list``
-------------------

.. method:: ModelResource.obj_delete_list(self, **kwargs)

A ORM-specific implementation of ``obj_delete_list``.

Takes optional ``kwargs``, which can be used to narrow the query.

``obj_delete``
--------------

.. method:: ModelResource.obj_delete(self, **kwargs)

A ORM-specific implementation of ``obj_delete``.

Takes optional ``kwargs``, which are used to narrow the query to find
the instance.

``rollback``
------------

.. method:: ModelResource.rollback(self, bundles)

A ORM-specific implementation of ``rollback``.

Given the list of bundles, delete all models pertaining to those
bundles.

``save_m2m``
------------

.. method:: ModelResource.save_m2m(self, bundle)

Handles the saving of related M2M data.

Due to the way Django works, the M2M data must be handled after the
main instance, which is why this isn't a part of the main ``save`` bits.

Currently slightly inefficient in that it will clear out the whole
relation and recreate the related data as needed.

``get_resource_uri``
--------------------

.. method:: ModelResource.get_resource_uri(self, bundle_or_obj)

Handles generating a resource URI for a single resource.

Uses the model's ``pk`` in order to create the URI.
