.. _ref-tools:

=====
Tools
=====

Here are some tools that might help in interacting with the API that Tastypie
provides:


Browser
=======

JSONView
--------

* Firefox - https://addons.mozilla.org/en-US/firefox/addon/jsonview/
* Chrome - https://chrome.google.com/webstore/detail/chklaanhfefbnpoihckbnefhakgolnmc

A plugin (actually two different ones that closely mirror each other) that
nicely reformats JSON data in the browser.


Extensions
==========

Tastypie-msgpack
----------------

https://github.com/stephenmcd/tastypie-msgpack

Adds MsgPack_ support to Tastypie's serializer.

.. _MsgPack: http://msgpack.org/


Python
======

Slumber
-------

http://slumber.in/

Slumber is a small Python library that makes it easy to access & work with
APIs. It works for many others, but works especially well with Tastypie.

Hammock
-------

https://github.com/kadirpekel/hammock

Hammock is a fun module lets you deal with rest APIs by converting them into dead simple programmatic APIs.
It uses popular ``requests`` module in backyard to provide full-fledged rest experience.

Here is what it looks like::

    >>> import hammock
    >>> api = hammock.Hammock('http://localhost:8000')
    >>> api.users('foo').posts('bar').comments.GET()
    <Response [200]>

drest
-----

http://drest.rtfd.org/

drest is another small Python library. It focuses on extensibility & can also
work with many different API, with an emphasis on Tastypie.


json.tool
---------

Included with Python, this tool makes reformatting JSON easy. For example::

    $ curl http://localhost:8000/api/v1/note/ | python -m json.tool

Will return nicely reformatted data like::

    {
        "meta": {
            "total_count": 1
        },
        "objects": [
            {
                "content": "Hello world!",
                "user": "/api/v1/user/1/"
            }
        ]
    }


django-permissionsx
-------------------

https://github.com/thinkingpotato/django-permissionsx

This package allows using one set of rules both for Django class-based views]
and Tastypie authorization. For example:

**articles/permissions.py**::

    class StaffPermissions(Permissions):
        permissions = P(profile__is_editor=True) | P(profile__is_administrator=True)

**articles/views.py**::

    class ArticleDeleteView(PermissionsViewMixin, DeleteView):
        model = Article
        success_url = reverse_lazy('article_list')
        permissions = StaffPermissions

**articles/api.py**::

    class StaffOnlyAuthorization(PermissionsAuthorization):
        permissions = StaffPermissions


django-superbulk
----------------

https://github.com/thelonecabbage/django-superbulk

This app adds bulk operation support to any Django view-based app, allowing for
better transactional behavior.



Javascript
==========

backbone-tastypie
-----------------

https://github.com/PaulUithol/backbone-tastypie

A small layer that makes Backbone & Tastypie plan nicely together.


backbone-relational
-------------------

https://github.com/PaulUithol/Backbone-relational/

Allows Backbone to work with relational data, like the kind of data Tastypie
provides.

