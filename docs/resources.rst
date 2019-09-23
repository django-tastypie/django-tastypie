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
source. Hooking up things like a NoSQL store (see :doc:`non_orm_data_sources`),
a search solution like Haystack or even managed filesystem data are all good
use cases for ``Resource`` knowing nothing about the ORM.


Flow Through The Request/Response Cycle
=======================================

Tastypie can be thought of as a set of class-based views that provide the API
functionality. As such, many part of the request/response cycle are standard
Django behaviors. For instance, all routing/middleware/response-handling aspects
are the same as a typical Django app. Where it differs is in the view itself.

As an example, we'll walk through what a GET request to a list endpoint (say
``/api/v1/user/?format=json``) looks like:

* The ``Resource.urls`` are checked by Django's url resolvers.
* On a match for the list view, ``Resource.wrap_view('dispatch_list')`` is
  called. ``wrap_view`` provides basic error handling & allows for returning
  serialized errors.
* Because ``dispatch_list`` was passed to ``wrap_view``,
  ``Resource.dispatch_list`` is called next. This is a thin wrapper around
  ``Resource.dispatch``.
* ``dispatch`` does a bunch of heavy lifting. It ensures:

  * the requested HTTP method is in ``allowed_methods`` (``method_check``),
  * the class has a method that can handle the request (``get_list``),
  * the user is authenticated (``is_authenticated``),
  * & the user has not exceeded their throttle (``throttle_check``).

  At this point, ``dispatch`` actually calls the requested method (``get_list``).

* ``get_list`` does the actual work of the API. It does:

  * A fetch of the available objects via ``Resource.obj_get_list``. In the case
    of ``ModelResource``, this builds the ORM filters to apply
    (``ModelResource.build_filters``). It then gets the ``QuerySet`` via
    ``ModelResource.get_object_list`` (which performs
    ``Resource.authorized_read_list`` to possibly limit the set the user
    can work with) and applies the built filters to it.
  * It then sorts the objects based on user input
    (``ModelResource.apply_sorting``).
  * Then it paginates the results using the supplied ``Paginator`` & pulls out
    the data to be serialized.
  * The objects in the page have ``full_dehydrate`` applied to each of them,
    causing Tastypie to translate the raw object data into the fields the
    endpoint supports.
  * Finally, it calls ``Resource.create_response``.

* ``create_response`` is a shortcut method that:

  * Determines the desired response format (``Resource.determine_format``),
  * Serializes the data given to it in the proper format,
  * And returns a Django ``HttpResponse`` (200 OK) with the serialized data.

* We bubble back up the call stack to ``dispatch``. The last thing ``dispatch``
  does is potentially store that a request occurred for future throttling
  (``Resource.log_throttled_access``) then either returns the ``HttpResponse``
  or wraps whatever data came back in a response (so Django doesn't freak out).

Processing on other endpoints or using the other HTTP methods results in a
similar cycle, usually differing only in what "actual work" method gets called
(which follows the format of "``<http_method>_<list_or_detail>``"). In the case
of POST/PUT, the ``hydrate`` cycle additionally takes place and is used to take
the user data & convert it to raw data for storage.


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


Accessing The Current Request
=============================

Being able to change behavior based on the current request is a very common
need. Virtually anywhere within ``Resource/ModelResource``, if a ``bundle`` is
available, you can access it using ``bundle.request``. This is useful for
altering querysets, ensuring headers are present, etc.

Most methods you may need to override/extend should get a ``bundle`` passed to
them.

If you're using the ``Resource/ModelResource`` directly, with no ``request``
available, an empty ``Request`` will be supplied instead. If this is a common
pattern/usage in your code, you'll want to accommodate for data that potentially
isn't there.


Advanced Data Preparation
=========================

Not all data can be easily pulled off an object/model attribute. And sometimes,
you (or the client) may need to send data that doesn't neatly fit back into the
data model on the server side. For this, Tastypie has the "dehydrate/hydrate"
cycle.

The Dehydrate Cycle
-------------------

Tastypie uses a "dehydrate" cycle to prepare data for serialization, which is
to say that it takes the raw, potentially complicated data model & turns it
into a (generally simpler) processed data structure for client consumption.
This usually means taking a complex data object & turning it into a dictionary
of simple data types.

Broadly speaking, this takes the ``bundle.obj`` instance & builds
``bundle.data``, which is what is actually serialized.

The cycle looks like:

* Put the data model into a ``Bundle`` instance, which is then passed through
  the various methods.
* Run through all fields on the ``Resource``, letting each field
  perform its own ``dehydrate`` method on the ``bundle``.
* While processing each field, look for a ``dehydrate_<fieldname>`` method on
  the ``Resource``. If it's present, call it with the ``bundle``.
* Finally, after all fields are processed, if the ``dehydrate`` method is
  present on the ``Resource``, it is called & given the entire ``bundle``.

The goal of this cycle is to populate the ``bundle.data`` dictionary with data
suitable for serialization. With the exception of the ``alter_*`` methods (as
hooks to manipulate the overall structure), this cycle controls what is
actually handed off to be serialized & sent to the client.

Per-field ``dehydrate``
~~~~~~~~~~~~~~~~~~~~~~~

Each field (even custom ``ApiField`` subclasses) has its own ``dehydrate``
method. If it knows how to access data (say, given the ``attribute`` kwarg), it
will attempt to populate values itself.

The return value is put in the ``bundle.data`` dictionary (by the ``Resource``)
with the fieldname as the key.

``dehydrate_FOO``
~~~~~~~~~~~~~~~~~

Since not all data may be ready for consumption based on just attribute access
(or may require an advanced lookup/calculation), this hook enables you to fill
in data or massage whatever the field generated.

.. note::

  The ``FOO`` here is not literal. Instead, it is a placeholder that should be
  replaced with the fieldname in question.

Defining these methods is especially common when deserializing related data,
providing statistics or filling in unrelated data.

A simple example::

    class MyResource(ModelResource):
        # The ``title`` field is already added to the class by ``ModelResource``
        # and populated off ``Note.title``. But we want allcaps titles...

        class Meta:
            queryset = Note.objects.all()

        def dehydrate_title(self, bundle):
            return bundle.data['title'].upper()

A complex example::

    class MyResource(ModelResource):
        # As is, this is just an empty field. Without the ``dehydrate_rating``
        # method, no data would be populated for it.
        rating = fields.FloatField(readonly=True)

        class Meta:
            queryset = Note.objects.all()

        def dehydrate_rating(self, bundle):
            total_score = 0.0

            # Make sure we don't have to worry about "divide by zero" errors.
            if not bundle.obj.rating_set.count():
                return total_score

            # We'll run over all the ``Rating`` objects & calculate an average.
            for rating in bundle.obj.rating_set.all():
                total_score += rating.rating

            return total_score /  bundle.obj.rating_set.count()

The return value is updated in the ``bundle.data``. You should avoid altering
``bundle.data`` here if you can help it.

``dehydrate``
~~~~~~~~~~~~~

The ``dehydrate`` method takes a now fully-populated ``bundle.data`` & make
any last alterations to it. This is useful for when a piece of data might
depend on more than one field, if you want to shove in extra data that isn't
worth having its own field or if you want to dynamically remove things from
the data to be returned.

A simple example::

    class MyResource(ModelResource):
        class Meta:
            queryset = Note.objects.all()

        def dehydrate(self, bundle):
            # Include the request IP in the bundle.
            bundle.data['request_ip'] = bundle.request.META.get('REMOTE_ADDR')
            return bundle

A complex example::

    class MyResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            excludes = ['email', 'password', 'is_staff', 'is_superuser']

        def dehydrate(self, bundle):
            # If they're requesting their own record, add in their email address.
            if bundle.request.user.pk == bundle.obj.pk:
                # Note that there isn't an ``email`` field on the ``Resource``.
                # By this time, it doesn't matter, as the built data will no
                # longer be checked against the fields on the ``Resource``.
                bundle.data['email'] = bundle.obj.email

            return bundle

This method should return a ``bundle``, whether it modifies the existing one or creates a whole new one. You can even remove any/all data from the
``bundle.data`` if you wish.

The Hydrate Cycle
-------------------

Tastypie uses a "hydrate" cycle to take serialized data from the client
and turn it into something the data model can use. This is the reverse process
from the ``dehydrate`` cycle. In fact, by default, Tastypie's serialized data
should be "round-trip-able", meaning the data that comes out should be able to
be fed back in & result in the same original data model. This usually means
taking a dictionary of simple data types & turning it into a complex data
object.

Broadly speaking, this takes the recently-deserialized ``bundle.data``
dictionary & builds ``bundle.obj`` (but does **NOT** save it).

The cycle looks like:

* Put the data from the client into a ``Bundle`` instance, which is then passed
  through the various methods.
* If the ``hydrate`` method is present on the ``Resource``, it is called & given the entire ``bundle``.
* Then run through all fields on the ``Resource``, look for a ``hydrate_<fieldname>`` method on
  the ``Resource``. If it's present, call it with the ``bundle``.
* Finally after all other processing is done, while processing each field, let each field
  perform its own ``hydrate`` method on the ``bundle``.

The goal of this cycle is to populate the ``bundle.obj`` data model with data
suitable for saving/persistence. Again, with the exception of the ``alter_*``
methods (as hooks to manipulate the overall structure), this cycle controls
how the data from the client is interpreted & placed on the data model.

``hydrate``
~~~~~~~~~~~

The ``hydrate`` method allows you to make initial changes to the ``bundle.obj``.
This includes things like prepopulating fields you don't expose over the API,
recalculating related data or mangling data.

Example::

    class MyResource(ModelResource):
        # The ``title`` field is already added to the class by ``ModelResource``
        # and populated off ``Note.title``. We'll use that title to build a
        # ``Note.slug`` as well.

        class Meta:
            queryset = Note.objects.all()

        def hydrate(self, bundle):
            # Don't change existing slugs.
            # In reality, this would be better implemented at the ``Note.save``
            # level, but is for demonstration.
            if not bundle.obj.pk:
                bundle.obj.slug = slugify(bundle.data['title'])

            return bundle

This method should return a ``bundle``, whether it modifies the existing one or
creates a whole new one. You can even remove any/all data from the
``bundle.obj`` if you wish.

``hydrate_FOO``
~~~~~~~~~~~~~~~

Data from the client may not map directly onto the data model or might need
augmentation. This hook lets you take that data & convert it.

.. note::

  The ``FOO`` here is not literal. Instead, it is a placeholder that should be
  replaced with the fieldname in question.

A simple example::

    class MyResource(ModelResource):
        # The ``title`` field is already added to the class by ``ModelResource``
        # and populated off ``Note.title``. But we want lowercase titles...

        class Meta:
            queryset = Note.objects.all()

        def hydrate_title(self, bundle):
            bundle.data['title'] = bundle.data['title'].lower()
            return bundle

The return value is the ``bundle``.

Per-field ``hydrate``
~~~~~~~~~~~~~~~~~~~~~

Each field (even custom ``ApiField`` subclasses) has its own ``hydrate``
method. If it knows how to access data (say, given the ``attribute`` kwarg), it
will attempt to take data from the ``bundle.data`` & assign it on the data
model.

The return value is put in the ``bundle.obj`` attribute for that fieldname.


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
  is ``['get', 'post', 'put', 'delete', 'patch']``. Set it to an empty list
  (i.e. `[]`) to disable all methods.


.. _detail-allowed-methods:

``detail_allowed_methods``
--------------------------

  Controls what detail REST methods the ``Resource`` should respond to. Default
  is ``['get', 'post', 'put', 'delete', 'patch']``. Set it to an empty list
  (i.e. `[]`) to disable all methods.

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

  Specifies the fields that the ``Resource`` will accept client filtering on.
  Default is ``{}``.

  Keys should be the fieldnames as strings while values should be a list of
  accepted filter types.

  This also restricts what fields can be filtered on when manually
  calling ``obj_get`` and ``obj_get_list``.

``ordering``
------------

  Specifies the what fields the ``Resource`` should allow ordering on.
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
  are date/time related. Please see the :doc:`cookbook` for a way around this.

``abstract``
------------

  In concrete ``Resource`` and ``ModelResource`` instances, either
  ``object_class`` or ``queryset`` is required.
  If you wish to build an abstract base ``Resource`` class, you can bypass
  this requirement by setting ``abstract`` to ``True``.

``fields``
----------

  Controls what introspected fields the ``Resource`` should include.
  A whitelist of fields. Default is ``None``.

  The default value of ``None`` means that all Django fields will be
  introspected. In order to specify that no fields should be introspected,
  use ``[]``

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

  If ``False``, ``HttpNoContent`` (204) is returned on ``PUT``
  with an empty body & a ``Location`` header of where to request the full
  resource.

  If ``True``, ``HttpResponse`` (200) is returned on ``POST/PUT``
  with a body containing all the data in a serialized form.

``collection_name``
-------------------

  Specifies the collection of objects returned in the ``GET`` list will be
  named. Default is ``objects``.

``detail_uri_name``
-------------------

  Specifies the name for the regex group that matches on detail views. Defaults
  to ``pk``.


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

Valid filtering values are: `Django ORM filters`_ (e.g. ``startswith``,
``exact``, ``lte``, etc.) or the ``ALL`` or ``ALL_WITH_RELATIONS`` constants
defined in :mod:`tastypie.constants`.

.. _Django ORM filters: https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups

These filters will be extracted from URL query strings using the same
double-underscore syntax as the Django ORM::

    /api/v1/myresource/?slug=myslug
    /api/v1/myresource/?slug__startswith=test


Advanced Filtering
==================

If you need to filter things other than ORM resources or wish to apply
additional constraints (e.g. text filtering using `django-haystack
<http://haystacksearch.org/>`_ rather than simple database queries) your
:class:`~tastypie.resources.Resource` may define a custom
:meth:`~tastypie.resource.Resource.build_filters` method which allows you to
filter the queryset before processing a request::

    from haystack.query import SearchQuerySet

    class MyResource(Resource):
        def build_filters(self, filters=None, **kwargs):
            if filters is None:
                filters = {}

            orm_filters = super(MyResource, self).build_filters(filters, **kwargs)

            if "q" in filters:
                sqs = SearchQuerySet().auto_query(filters['q'])

                orm_filters["pk__in"] = [i.pk for i in sqs]

            return orm_filters


Using PUT/DELETE/PATCH In Unsupported Places
============================================

Some places, like in certain browsers or hosts, don't allow the
``PUT/DELETE/PATCH`` methods. In these environments, you can simulate those
kinds of requests by providing an ``X-HTTP-Method-Override`` header. For
example, to send a ``PATCH`` request over ``POST``, you'd send a request like::

    curl --dump-header - -H "Content-Type: application/json" -H "X-HTTP-Method-Override: PATCH" -X POST --data '{"title": "I Visited Grandma Today"}' http://localhost:8000/api/v1/entry/1/


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

``get_response_class_for_exception``
------------------------------------

.. method:: Resource.get_response_class_for_exception(self, request, exception)

Can be overridden to customize response classes used for uncaught exceptions.
Should always return a subclass of``django.http.HttpResponse``.

``base_urls``
-------------

.. method:: Resource.base_urls(self)

The standard URLs this ``Resource`` should respond to. These include the
list, detail, schema & multiple endpoints by default.

Should return a list of individual URLconf lines.

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

Should return a list of individual URLconf lines.

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
sent. Occurs after any dehydration has by applied.

As such this is a useful place to apply modifications which affect many
list elements.

Example::

    def alter_list_data_to_serialize(self, request, data):
        bar = some_expensive_call()
        for obj in data['objects']:
            obj.foo = bar
        return data

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

Populate the bundle's :attr:`data` attribute.

The ``bundle`` parameter will have the data that needs dehydrating in its
:attr:`obj` attribute.

The ``for_list`` parameter indicates the style of response being prepared:
    - ``True`` indicates a list of items. Note that :meth:`full_dehydrate` will
      be called once for each object requested.
    - ``False`` indicates a response showing the details for an item

This method is responsible for invoking the :meth:`dehydrate` method of
all the fields in the resource. Additionally, it calls
:meth:`Resource.dehydrate`.

Must return a :class:`Bundle` with the desired dehydrated :attr:`data`
(usually a :class:`dict`). Typically one should modify the bundle passed in
and return it, but you may also return a completely new bundle.


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

Return ``HttpAccepted`` (200 OK) if
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
``Meta.always_return_data = True``, return ``HttpAccepted`` (200
OK).

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
    to an existing resource then the item is an update; it's treated
    like a ``PATCH`` to the corresponding resource detail.

  * If the dict has a ``resource_uri`` but the resource *doesn't* exist,
    then this is considered to be a create-via-``PUT``.

Each entry in ``deleted_objects`` refers to a resource URI of an existing
resource to be deleted; each is handled like a ``DELETE`` to the relevant
resource.

In any case:

  * If there's a resource URI it *must* refer to a resource of this
    type. It's an error to include a URI of a different resource.

  * ``PATCH`` is all or nothing. If a single sub-operation fails, the
    entire request will fail and all resources will be rolled back.

  * For ``PATCH`` to work, you **must** have ``patch`` in your
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

``check_filtering``
-------------------

.. method:: ModelResource.check_filtering(self, field_name, filter_type='exact', filter_bits=None)

Given a field name, an optional filter type and an optional list of
additional relations, determine if a field can be filtered on.

If a filter does not meet the needed conditions, it should raise an
``InvalidFilterError``.

If the filter meets the conditions, a list of attribute names (not
field names) will be returned.

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

``apply_filters``
-----------------

.. method:: ModelResource.apply_filters(self, request, applicable_filters)

An ORM-specific implementation of ``apply_filters``.

The default simply applies the ``applicable_filters`` as ``**kwargs``,
but should make it possible to do more advanced things.

``get_object_list``
-------------------

.. method:: ModelResource.get_object_list(self, request)

A ORM-specific implementation of ``get_object_list``.

Returns a ``QuerySet`` that may have been limited by other overrides.

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

``obj_delete_list_for_update``
------------------------------

.. method:: ModelResource.obj_delete_list_for_update(self, **kwargs)

A ORM-specific implementation of ``obj_delete_list_for_update``.

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

``save_related``
----------------

.. method:: ModelResource.save_related(self, bundle)

Handles the saving of related non-M2M data.

Calling assigning ``child.parent = parent`` & then calling
``Child.save`` isn't good enough to make sure the ``parent``
is saved.

To get around this, we go through all our related fields &
call ``save`` on them if they have related, non-M2M data.
M2M data is handled by the ``ModelResource.save_m2m`` method.

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
