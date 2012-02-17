.. _ref-interacting:

========================
Interacting With The API
========================

Now that you've got a shiny new REST-style API in place, let's demonstrate how
to interact with it. We'll assume that you have cURL_ installed on your system
(generally available on most modern Mac & Linux machines), but any tool that
allows you to control headers & bodies on requests will do.

.. _cURL: http://curl.haxx.se/

We'll assume that we're interacting with the following Tastypie code::

    # myapp/api/resources.py
    from django.contrib.auth.models import User
    from tastypie.authorization import Authorization
    from tastypie import fields
    from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
    from myapp.models import Entry


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'user'
            excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
            filtering = {
                'username': ALL,
            }


    class EntryResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user')

        class Meta:
            queryset = Entry.objects.all()
            resource_name = 'entry'
            authorization = Authorization()
            filtering = {
                'user': ALL_WITH_RELATIONS,
                'pub_date': ['exact', 'lt', 'lte', 'gte', 'gt'],
            }


    # urls.py
    from django.conf.urls.defaults import *
    from tastypie.api import Api
    from myapp.api.resources import EntryResource, UserResource

    v1_api = Api(api_name='v1')
    v1_api.register(UserResource())
    v1_api.register(EntryResource())

    urlpatterns = patterns('',
        # The normal jazz here...
        (r'^blog/', include('myapp.urls')),
        (r'^api/', include(v1_api.urls)),
    )

Let's fire up a shell & start exploring the API!


Front Matter
============

Tastypie tries to treat all clients & all serialization types as equally as
possible. It also tries to be a good 'Net citizen & respects the HTTP method
used as well as the ``Accepts`` headers sent. Between these two, you control
all interactions with Tastypie through relatively few endpoints.

.. warning::

  Should you try these URLs in your browser, be warned you **WILL** need to
  append ``?format=json`` (or ``xml`` or ``yaml``) to the URL. Your browser
  requests ``application/xml`` before ``application/json``, so you'll always
  get back XML if you don't specify it.

  That's also why it's recommended that you explore via curl, because you
  avoid your browser's opinionated requests & get something closer to what
  any programmatic clients will get.


Fetching Data
=============

Since reading data out of an API is a very common activity (and the easiest
type of request to make), we'll start there. Tastypie tries to expose various
parts of the API & interlink things within the API (HATEOAS).

Api-Wide
--------

We'll start at the highest level::

    curl http://localhost:8000/api/v1/

You'll get back something like::

    {
        "entry": {
            "list_endpoint": "/api/v1/entry/",
            "schema": "/api/v1/entry/schema/"
        },
        "user": {
            "list_endpoint": "/api/v1/user/",
            "schema": "/api/v1/user/schema/"
        }
    }

This lists out all the different ``Resource`` classes you registered in your
URLconf with the API. Each one is listed by the ``resource_name`` you gave it
and provides the ``list_endpoint`` & the ``schema`` for the resource.

Note that these links try to direct you to other parts of the API, to make
exploration/discovery easier. We'll use these URLs in the next several
sections.

To demonstrate another format, you could run the following to get the XML
variant of the same information::

    curl -H "Accept: application/xml" http://localhost:8000/api/v1/

To which you'd receive::

    <?xml version="1.0" encoding="utf-8"?>
    <response>
      <entry type="hash">
        <list_endpoint>/api/v1/entry/</list_endpoint>
        <schema>/api/v1/entry/schema/</schema>
      </entry>
      <user type="hash">
        <list_endpoint>/api/v1/user/</list_endpoint>
        <schema>/api/v1/user/schema/</schema>
      </user>
    </response>

We'll stick to JSON for the rest of this document, but using XML should be OK
to do at any time.


.. _schema-inspection:

Inspecting The Resource's Schema
--------------------------------

Since the api-wide view gave us a ``schema`` URL, let's inspect that next.
We'll use the ``entry`` resource. Again, a simple GET request by curl::

    curl http://localhost:8000/api/v1/entry/schema/

This time, we get back a lot more data::

    {
        "default_format": "application/json",
        "fields": {
            "body": {
                "help_text": "Unicode string data. Ex: \"Hello World\"",
                "nullable": false,
                "readonly": false,
                "type": "string"
            },
            "id": {
                "help_text": "Unicode string data. Ex: \"Hello World\"",
                "nullable": false,
                "readonly": false,
                "type": "string"
            },
            "pub_date": {
                "help_text": "A date & time as a string. Ex: \"2010-11-10T03:07:43\"",
                "nullable": false,
                "readonly": false,
                "type": "datetime"
            },
            "resource_uri": {
                "help_text": "Unicode string data. Ex: \"Hello World\"",
                "nullable": false,
                "readonly": true,
                "type": "string"
            },
            "slug": {
                "help_text": "Unicode string data. Ex: \"Hello World\"",
                "nullable": false,
                "readonly": false,
                "type": "string"
            },
            "title": {
                "help_text": "Unicode string data. Ex: \"Hello World\"",
                "nullable": false,
                "readonly": false,
                "type": "string"
            },
            "user": {
                "help_text": "A single related resource. Can be either a URI or set of nested resource data.",
                "nullable": false,
                "readonly": false,
                "type": "related"
            }
        },
        "filtering": {
            "pub_date": ["exact", "lt", "lte", "gte", "gt"],
            "user": 2
        }
    }

This lists out the ``default_format`` this resource responds with, the
``fields`` on the resource & the ``filtering`` options available. This
information can be used to prepare the other aspects of the code for the
data it can obtain & ways to filter the resources.


Getting A Collection Of Resources
---------------------------------

Let's get down to fetching live data. From the api-wide view, we'll hit
the ``list_endpoint`` for ``entry``::

    curl http://localhost:8000/api/v1/entry/

We get back data that looks like::

    {
        "meta": {
            "limit": 20,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 3
        },
        "objects": [{
            "body": "Welcome to my blog!",
            "id": "1",
            "pub_date": "2011-05-20T00:46:38",
            "resource_uri": "/api/v1/entry/1/",
            "slug": "first-post",
            "title": "First Post",
            "user": "/api/v1/user/1/"
        },
        {
            "body": "Well, it's been awhile and I still haven't updated. ",
            "id": "2",
            "pub_date": "2011-05-21T00:46:58",
            "resource_uri": "/api/v1/entry/2/",
            "slug": "second-post",
            "title": "Second Post",
            "user": "/api/v1/user/1/"
        },
        {
            "body": "I'm really excited to get started with this new blog. It's gonna be great!",
            "id": "3",
            "pub_date": "2011-05-20T00:47:30",
            "resource_uri": "/api/v1/entry/3/",
            "slug": "my-blog",
            "title": "My Blog",
            "user": "/api/v1/user/2/"
        }]
    }

Some things to note:

  * By default, you get a paginated set of objects (20 per page is the default).
  * In the ``meta``, you get a ``previous`` & ``next``. If available, these are
    URIs to the previous & next pages.
  * You get a list of resources/objects under the ``objects`` key.
  * Each resources/object has a ``resource_uri`` field that points to the
    detail view for that object.
  * The foreign key to ``User`` is represented as a URI by default. If you're
    looking for the full ``UserResource`` to be embedded in this view, you'll
    need to add ``full=True`` to the ``fields.ToOneField``.

If you want to skip paginating, simply run::

    curl http://localhost:8000/api/v1/entry/?limit=0

Be warned this will return all objects, so it may be a CPU/IO-heavy operation
on large datasets.

Let's try filtering on the resource. Since we know we can filter on the
``user``, we'll fetch all posts by the ``daniel`` user with::

    curl http://localhost:8000/api/v1/entry/?user__username=daniel

We get back what we asked for::

    {
        "meta": {
            "limit": 20,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 2
        },
        "objects": [{
            "body": "Welcome to my blog!",
            "id": "1",
            "pub_date": "2011-05-20T00:46:38",
            "resource_uri": "/api/v1/entry/1/",
            "slug": "first-post",
            "title": "First Post",
            "user": "/api/v1/user/1/"
        },
        {
            "body": "Well, it's been awhile and I still haven't updated. ",
            "id": "2",
            "pub_date": "2011-05-21T00:46:58",
            "resource_uri": "/api/v1/entry/2/",
            "slug": "second-post",
            "title": "Second Post",
            "user": "/api/v1/user/1/"
        }]
    }

Where there were three posts before, now there are only two.


Getting A Detail Resource
-------------------------

Since each resource/object in the list view had a ``resource_uri``, let's
explore what's there::

    curl http://localhost:8000/api/v1/entry/1/

We get back a similar set of data that we received from the list view::

    {
        "body": "Welcome to my blog!",
        "id": "1",
        "pub_date": "2011-05-20T00:46:38",
        "resource_uri": "/api/v1/entry/1/",
        "slug": "first-post",
        "title": "First Post",
        "user": "/api/v1/user/1/"
    }

Where this proves useful (for example) is present in the data we got back. We
know the URI of the ``User`` associated with this blog entry. Let's run::

    curl http://localhost:8000/api/v1/user/1/

Without ever seeing any aspect of the ``UserResource`` & just following the URI
given, we get back::

    {
        "date_joined": "2011-05-20T00:42:14.990617",
        "first_name": "",
        "id": "1",
        "last_login": "2011-05-20T00:44:57.510066",
        "last_name": "",
        "resource_uri": "/api/v1/user/1/",
        "username": "daniel"
    }

You can do a similar fetch using the following Javascript/jQuery (though be
wary of same-domain policy)::

    $.ajax({
      url: 'http://localhost:8000/api/v1/user/1/',
      type: 'GET',
      accepts: 'application/json',
      dataType: 'json'
    })


Selecting A Subset Of Resources
-------------------------------

Sometimes you may want back more than one record, but not an entire list view
nor do you want to do multiple requests. Tastypie includes a "set" view, which
lets you cherry-pick the objects you want. For example, if we just want the
first & third ``Entry`` resources, we'd run::

    curl "http://localhost:8000/api/v1/entry/set/1;3/"

.. note::

  Quotes are needed in this case because of the semicolon delimiter between
  primary keys. Without the quotes, bash tries to split it into two statements.
  No extraordinary quoting will be necessary in your application (unless your
  API client is written in bash :D).

And we get back just those two objects::

    {
        "objects": [{
            "body": "Welcome to my blog!",
            "id": "1",
            "pub_date": "2011-05-20T00:46:38",
            "resource_uri": "/api/v1/entry/1/",
            "slug": "first-post",
            "title": "First Post",
            "user": "/api/v1/user/1/"
        },
        {
            "body": "I'm really excited to get started with this new blog. It's gonna be great!",
            "id": "3",
            "pub_date": "2011-05-20T00:47:30",
            "resource_uri": "/api/v1/entry/3/",
            "slug": "my-blog",
            "title": "My Blog",
            "user": "/api/v1/user/2/"
        }]
    }

Note that, like the list view, you get back a list of ``objects``. Unlike the
list view, there is **NO** pagination applied to these objects. You asked for
them, you're going to get them all.


Sending Data
============

Tastypie also gives you full write capabilities in the API. Since the
``EntryResource`` has the no-limits ``Authentication`` & ``Authorization`` on
it, we can freely write data.

.. warning::

  Note that this is a huge security hole as well. Don't put unauthorized
  write-enabled resources on the Internet, because someone will trash your
  data.

  This is why ``ReadOnlyAuthorization`` is the default in Tastypie & why you
  must override to provide more access.

The good news is that there are no new URLs to learn. The "list" & "detail"
URLs we've been using to fetch data *ALSO* support the
``POST``/``PUT``/``DELETE`` HTTP methods.


Creating A New Resource (POST)
------------------------------

Let's add a new entry. To create new data, we'll switch from ``GET`` requests
to the familiar ``POST`` request.

.. note::

    Tastypie encourages "round-trippable" data, which means the data you
    can GET should be able to be POST/PUT'd back to recreate the same
    object.

    If you're ever in question about what you should send, do a GET on
    another object & see what Tastypie thinks it should look like.

To create new resources/objects, you will ``POST`` to the list endpoint of
a resource. Trying to ``POST`` to a detail endpoint has a different meaning in
the REST mindset (meaning to add a resource as a child of a resource of the
same type).

As with all Tastypie requests, the headers we request are important. Since
we've been using primarily JSON throughout, let's send a new entry in JSON
format::

    curl --dump-header - -H "Content-Type: application/json" -X POST --data '{"body": "This will prbbly be my lst post.", "pub_date": "2011-05-22T00:46:38", "slug": "another-post", "title": "Another Post", "user": "/api/v1/user/1/"}' http://localhost:8000/api/v1/entry/

The ``Content-Type`` header here informs Tastypie that we're sending it JSON.
We send the data as a JSON-serialized body (**NOT** as form-data in the form of
URL parameters). What we get back is the following response::

    HTTP/1.0 201 CREATED
    Date: Fri, 20 May 2011 06:48:36 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Type: text/html; charset=utf-8
    Location: http://localhost:8000/api/v1/entry/4/

You'll also note that we get a correct HTTP status code back (201) & a
``Location`` header, which gives us the URI to our newly created resource.

Passing ``--dump-header -`` is important, because it gives you all the headers
as well as the status code. When things go wrong, this will be useful
information to help with debugging. For instance, if we send a request without
a ``user``::

    curl --dump-header - -H "Content-Type: application/json" -X POST --data '{"body": "This will prbbly be my lst post.", "pub_date": "2011-05-22T00:46:38", "slug": "another-post", "title": "Another Post"}' http://localhost:8000/api/v1/entry/

We get back::

    HTTP/1.0 400 BAD REQUEST
    Date: Fri, 20 May 2011 06:53:02 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Type: text/html; charset=utf-8

    The 'user' field has no data and doesn't allow a default or null value.

You can do a similar POST using the following Javascript/jQuery (though be
wary of same-domain policy)::

    # This may require the ``json2.js`` library for older browsers.
    var data = JSON.stringify({
        "body": "This will prbbly be my lst post.",
        "pub_date": "2011-05-22T00:46:38",
        "slug": "another-post",
        "title": "Another Post"
    });

    $.ajax({
      url: 'http://localhost:8000/api/v1/entry/',
      type: 'POST',
      contentType: 'application/json',
      data: data,
      dataType: 'json',
      processData: false
    })


Updating An Existing Resource (PUT)
-----------------------------------

You might have noticed that we made some typos when we submitted the POST
request. We can fix this using a ``PUT`` request to the detail endpoint (modify
this instance of a resource).::

    curl --dump-header - -H "Content-Type: application/json" -X PUT --data '{"body": "This will probably be my last post.", "pub_date": "2011-05-22T00:46:38", "slug": "another-post", "title": "Another Post", "user": "/api/v1/user/1/"}' http://localhost:8000/api/v1/entry/4/

After fixing up the ``body``, we get back::

    HTTP/1.0 204 NO CONTENT
    Date: Fri, 20 May 2011 07:13:21 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8

We get a 204 status code, meaning our update was successful. We don't get
a ``Location`` header back because we did the ``PUT`` on a detail URL, which
presumably did not change.

.. note::

    A ``PUT`` request requires that the entire resource representation be enclosed. Missing fields may cause errors, or be filled in by default values. 


Partially Updating An Existing Resource (PATCH)
-----------------------------------------------

In some cases, you may not want to send the entire resource when updating. To update just a subset of the fields, we can send a ``PATCH`` request to the detail endpoint.::

    curl --dump-header - -H "Content-Type: application/json" -X PATCH --data '{"body": "This actually is my last post."}' http://localhost:8000/api/v1/entry/4/


To which we should get back::

    HTTP/1.0 202 ACCEPTED
    Date: Fri, 20 May 2011 07:13:21 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8


Updating A Whole Collection Of Resources (PUT)
----------------------------------------------

You can also, in rare circumstances, update an entire collection of objects.
By sending a ``PUT`` request to the list view of a resource, you can replace
the entire collection.

.. warning::

  This deletes all of the objects first, then creates the objects afresh. This
  is done because determining which objects are the same is actually difficult
  to get correct in the general case for all people.

Send a request like::

    curl --dump-header - -H "Content-Type: application/json" -X PUT --data '{"objects": [{"body": "Welcome to my blog!","id": "1","pub_date": "2011-05-20T00:46:38","resource_uri": "/api/v1/entry/1/","slug": "first-post","title": "First Post","user": "/api/v1/user/1/"},{"body": "I'm really excited to get started with this new blog. It's gonna be great!","id": "3","pub_date": "2011-05-20T00:47:30","resource_uri": "/api/v1/entry/3/","slug": "my-blog","title": "My Blog","user": "/api/v1/user/2/"}]}' http://localhost:8000/api/v1/entry/

And you'll get back a response like::

    HTTP/1.0 204 NO CONTENT
    Date: Fri, 20 May 2011 07:13:21 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8


Deleting Data
=============

No CRUD setup would be complete without the ability to delete resources/objects.
Deleting also requires significantly less complicated requests than
``POST``/``PUT``.


Deleting A Single Resource
--------------------------

We've decided that we don't like the entry we added & edited earlier. Let's
delete it (but leave the other objects alone)::

    curl --dump-header - -H "Content-Type: application/json" -X DELETE  http://localhost:8000/api/v1/entry/4/

Once again, we get back the "Accepted" response of a 204::

    HTTP/1.0 204 NO CONTENT
    Date: Fri, 20 May 2011 07:28:01 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8

If we request that resource, we get a 410 to show it's no longer there::

    curl --dump-header - http://localhost:8000/api/v1/entry/4/

    HTTP/1.0 410 GONE
    Date: Fri, 20 May 2011 07:29:02 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Type: text/html; charset=utf-8

Additionally, if we try to run the ``DELETE`` again (using the same original
command), we get the "Gone" response again::

    HTTP/1.0 410 GONE
    Date: Fri, 20 May 2011 07:30:00 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Type: text/html; charset=utf-8


Deleting A Whole Collection Of Resources
----------------------------------------

Finally, it's possible to remove an entire collection of resources. This is
as destructive as it sounds. Once again, we use the ``DELETE`` method, this
time on the entire list endpoint::

    curl --dump-header - -H "Content-Type: application/json" -X DELETE  http://localhost:8000/api/v1/entry/

As a response, we get::

    HTTP/1.0 204 NO CONTENT
    Date: Fri, 20 May 2011 07:32:51 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8

Hitting the list view::

    curl --dump-header - http://localhost:8000/api/v1/entry/

Gives us a 200 but no objects::

    {
        "meta": {
            "limit": 20,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 0
        },
        "objects": []
    }


Bulk Operations
===============

As an optimization, it is possible to do many creations, updates, and deletions to a collection in a single request by sending a ``PATCH`` to the list endpoint.::

    curl --dump-header - -H "Content-Type: application/json" -X PATCH --data '{"objects": [{"body": "Surprise! Another post!.", "pub_date": "2012-02-16T00:46:38", "slug": "yet-another-post", "title": "Yet Another Post"}], "deleted_objects": ["http://localhost:8000/api/v1/entry/4/"]}'  http://localhost:8000/api/v1/entry/

We should get back::

    HTTP/1.0 202 ACCEPTED
    Date: Fri, 16 Feb 2012 00:46:38 GMT
    Server: WSGIServer/0.1 Python/2.7
    Content-Length: 0
    Content-Type: text/html; charset=utf-8

The Accepted response means the server has accepted the request, but gives no details on the result. In order to see any created resources, we would need to do a get ``GET`` on the list endpoint. 

For detailed information on the format of a bulk request, see :ref:`patch-list`.


You Did It!
===========

That's a whirlwind tour of interacting with a Tastypie API. There's additional
functionality present, such as:

* ``POST``/``PUT`` the other supported content-types
* More filtering/``order_by``/``limit``/``offset`` tricks
* Using overridden URLconfs to support complex or non-PK lookups
* Authentication

But this grounds you in the basics & hopefully clarifies usage/debugging better.
