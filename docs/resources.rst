.. _ref-resources:

Resources
*********

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
  * the user is authorized (``is_authorized``),
  * & the user has not exceeded their throttle (``throttle_check``).

  At this point, ``dispatch`` actually calls the requested method (``get_list``).

* ``get_list`` does the actual work of the API. It does:

  * A fetch of the available objects via ``Resource.obj_get_list``. In the case
    of ``ModelResource``, this builds the ORM filters to apply
    (``ModelResource.build_filters``). It then gets the ``QuerySet`` via
    ``ModelResource.get_object_list`` (which performs
    ``Resource.apply_authorization_limits`` to possibly limit the set the user
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

Being able to change behavior based on the current request is a very commmon
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

Defining these methods is especially common when denormalizing related data,
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

This method should return a ``bundle``, whether it modifies the existing one or
creates a whole new one. You can even remove any/all data from the
``bundle.data`` if you wish.

The Hydrate Cycle
-------------------

Tastypie uses a "hydrate" cycle to take serializated data from the client
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
* If the ``hydrate`` method is present on the ``Resource``, it is called & given
  the entire ``bundle``.
* Then run through all fields on the ``Resource``, look for a
  ``hydrate_<fieldname>`` method on the ``Resource``. If it's present, call it
  with the ``bundle``.
* Finally after all other processing is done, while processing each field, let
  each field perform its own ``hydrate`` method on the ``bundle``.

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
      comments = fields.ToManyField('myapp.api.resources.CommentResource',
                                    'comments')

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
        def build_filters(self, filters=None):
            if filters is None:
                filters = {}

            orm_filters = super(MyResource, self).build_filters(filters)

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


Resource and ModelResource reference
====================================

For a complete reference of attributes and methods please refer to:

* :ref:`Resource reference <resource-reference>`
* :ref:`ModelResource reference <model-resource-reference>`
