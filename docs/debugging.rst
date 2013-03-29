.. ref-debugging:

==================
Debugging Tastypie
==================

There are some common problems people run into when using Tastypie for the first
time. Some of the common problems and things to try appear below.


"I'm getting XML output in my browser but I want JSON output!"
==============================================================

This is actually not a bug and JSON support is present in your ``Resource``.
This issue is that Tastypie respects the ``Accept`` header your browser sends.
Most browsers send something like::

    Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5

Note that ``application/xml`` comes first, which is a format that Tastypie
handles by default, hence why you receive XML.

If you use ``curl`` from the command line, you should receive JSON by default::

    curl http://localhost:8000/api/v1/

If you want JSON in the browser, simply append ``?format=json`` to your URL.
Tastypie always respects this override first, before it falls back to the
``Accept`` header.


"What's the format for a POST or PUT?"
======================================

You can view full schema for your resource through :ref:`schema-inspection`.

In general, Tastypie will accept resources in the same format as it gives you.
This means that you can see what any POST or PUT should look like by
performing a GET of that resource.

Creating a duplicate of an entry, using Python and Requests_::

    import requests
    import json

    response = requests.get('http://localhost:8000/api/v1/entry/1/')
    event = json.loads(response.content)

    del event['id'] # We want the server to assign a new id

    response = requests.post('http://localhost:8000/api/v1/entry/',
                             data=json.dumps(event),
                             headers={'content-type': 'application/json'})


The new event should be almost identical, with the exception of readonly
fields. This method may fail if your model has a unique constraint, or
otherwise fails validation.

This is less likely to happen on PUT, except for application logic changes
(e.g. a `last_update` field). The following two ``curl`` commands replace and
entry with an copy::

    curl -H 'Accept: application/json' 'http://localhost:8000/api/v1/entry/1/' | \
    curl -H 'Content-Type: application/json' -X PUT --data @- "http://localhost:8000/api/v1/entry/1/"

You can do this over an entire collection as well::

    curl -H 'Accept: application/json' 'http://localhost:8000/api/v1/entry/?limit=0' | \
    curl -H 'Content-Type: application/json' -X PUT --data @- "http://localhost:8000/api/v1/entry/"

.. _Requests: http://python-requests.org


"Why is my syncdb with superuser failing with a DatabaseError?"
===============================================================

More specifically, this specific ``DatabaseError``::

    django.db.utils.DatabaseError: no such table: tastypie_apikey

This is a side effect of the (disabled by default) ``create_api_key`` signal
as described in the :ref:`authentication` section of the
documentation when used in conjunction with South.

To work around this issue, you can disable the ``create_api_key`` signal
until you have completed running ``syncdb --migrate`` for the first time.
