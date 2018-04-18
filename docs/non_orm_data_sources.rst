.. _ref-non_orm_data_sources:

========================================
Using Tastypie With Non-ORM Data Sources
========================================

Much of this documentation demonstrates the use of Tastypie with Django's ORM.
You might think that Tastypie depended on the ORM, when in fact, it was
purpose-built to handle non-ORM data. This documentation should help you get
started providing APIs using other data sources.

Virtually all of the code that makes Tastypie actually process requests &
return data is within the ``Resource`` class. ``ModelResource`` is actually a
light wrapper around ``Resource`` that provides ORM-specific access. The
methods that ``ModelResource`` overrides are the same ones you'll need to
override when hooking up your data source.

Approach
========

When working with ``Resource``, many things are handled for you. All the
authentication/authorization/caching/serialization/throttling bits should work
as normal and Tastypie can support all the REST-style methods. Schemas &
discovery views all work the same as well.

What you don't get out of the box are the fields you're choosing to expose &
the lowest level data access methods. If you want a full read-write API, there
are nine methods you need to implement. They are:

* ``detail_uri_kwargs``
* ``get_object_list``
* ``obj_get_list``
* ``obj_get``
* ``obj_create``
* ``obj_update``
* ``obj_delete_list``
* ``obj_delete``
* ``rollback``

If read-only is all you're exposing, you can cut that down to four methods to
override.

Using Riak for MessageResource
==============================

As an example, we'll take integrating with Riak_ (a Dynamo-like NoSQL store)
since it has both a simple API and demonstrate what hooking up to a
non-relational datastore looks like::

    import riak

    from tastypie import fields
    from tastypie.authorization import Authorization
    from tastypie.resources import Resource

    # We need a generic object to shove data in/get data from.
    # Riak generally just tosses around dictionaries, so we'll lightly
    # wrap that.
    class RiakObject(object):
        def __init__(self, initial=None):
            self.__dict__['_data'] = {}

            if hasattr(initial, 'items'):
                self.__dict__['_data'] = initial

        def __getattr__(self, name):
            return self._data.get(name, None)

        def __setattr__(self, name, value):
            self.__dict__['_data'][name] = value

        def to_dict(self):
            return self._data


    class MessageResource(Resource):
        # Just like a Django ``Form`` or ``Model``, we're defining all the
        # fields we're going to handle with the API here.
        uuid = fields.CharField(attribute='uuid')
        user_uuid = fields.CharField(attribute='user_uuid')
        message = fields.CharField(attribute='message')
        created = fields.IntegerField(attribute='created')

        class Meta:
            resource_name = 'riak'
            object_class = RiakObject
            authorization = Authorization()

        # Specific to this resource, just to get the needed Riak bits.
        def _client(self):
            return riak.RiakClient()

        def _bucket(self):
            client = self._client()
            # Note that we're hard-coding the bucket to use. Fine for
            # example purposes, but you'll want to abstract this.
            return client.bucket('messages')

        # The following methods will need overriding regardless of your
        # data source.
        def detail_uri_kwargs(self, bundle_or_obj):
            kwargs = {}

            if isinstance(bundle_or_obj, Bundle):
                kwargs['pk'] = bundle_or_obj.obj.uuid
            else:
                kwargs['pk'] = bundle_or_obj.uuid

            return kwargs

        def get_object_list(self, request):
            query = self._client().add('messages')
            query.map("function(v) { var data = JSON.parse(v.values[0].data); return [[v.key, data]]; }")
            results = []

            for result in query.run():
                new_obj = RiakObject(initial=result[1])
                new_obj.uuid = result[0]
                results.append(new_obj)

            return results

        def obj_get_list(self, bundle, **kwargs):
            # Filtering disabled for brevity...
            return self.get_object_list(bundle.request)

        def obj_get(self, bundle, **kwargs):
            bucket = self._bucket()
            message = bucket.get(kwargs['pk'])
            return RiakObject(initial=message.get_data())

        def obj_create(self, bundle, **kwargs):
            bundle.obj = RiakObject(initial=kwargs)
            bundle = self.full_hydrate(bundle)
            bucket = self._bucket()
            new_message = bucket.new(bundle.obj.uuid, data=bundle.obj.to_dict())
            new_message.store()
            return bundle

        def obj_update(self, bundle, **kwargs):
            return self.obj_create(bundle, **kwargs)

        def obj_delete_list(self, bundle, **kwargs):
            bucket = self._bucket()

            for key in bucket.get_keys():
                obj = bucket.get(key)
                obj.delete()

        def obj_delete(self, bundle, **kwargs):
            bucket = self._bucket()
            obj = bucket.get(kwargs['pk'])
            obj.delete()

        def rollback(self, bundles):
            pass

This represents a full, working, Riak-powered API endpoint. All REST-style
actions (GET/POST/PUT/DELETE) work correctly. The only shortcut taken in
this example was skipping filter-abilty, as adding in the MapReduce bits would
have decreased readability.

All said and done, just nine methods needed overriding, eight of which were
highly specific to how data access is done.

.. _Riak: https://pypi.python.org/pypi/riak
