Welcome to Tastypie!
====================

Tastypie is a webservice API framework for Django. It provides a convenient,
yet powerful and highly customizable, abstraction for creating REST-style
interfaces.

.. toctree::
   :maxdepth: 1

   tutorial
   interacting
   settings
   non_orm_data_sources
   tools
   testing
   compatibility_notes
   python3

   resources
   bundles
   api
   fields
   caching
   validation
   authentication
   authorization
   serialization
   throttling
   paginator
   geodjango
   content_types
   namespaces

   cookbook
   debugging
   who_uses
   contributing

.. toctree::
   :maxdepth: 2

   release_notes/index


Quick Start
===========

1. Add ``tastypie`` to ``INSTALLED_APPS``.
2. Create an ``api`` directory in your app with a bare ``__init__.py``.
3. Create an ``<my_app>/api/resources.py`` file and place the following in it::

    from tastypie.resources import ModelResource
    from my_app.models import MyModel


    class MyModelResource(ModelResource):
        class Meta:
            queryset = MyModel.objects.all()
            allowed_methods = ['get']

4. In your root URLconf, add the following code (around where the admin code might be)::

    from django.urls.conf import re_path, include
    from tastypie.api import Api
    from my_app.api.resources import MyModelResource

    v1_api = Api(api_name='v1')
    v1_api.register(MyModelResource())

    urlpatterns = [
      # ...more URLconf bits here...
      # Then add:
      re_path(r'^api/', include(v1_api.urls)),
    ]

5. Hit http://localhost:8000/api/v1/?format=json in your browser!


Requirements
============

Core
----

* Python 3.6+, preferably 3.8+ (Whatever is supported by your version of Django)
* Django 2.2, 3.2 (LTS releases) or Django 4.0 (latest release)
* dateutil (http://labix.org/python-dateutil) >= 2.1

Format Support
--------------

* XML: lxml 3 (http://lxml.de/) and defusedxml (https://pypi.python.org/pypi/defusedxml)
* YAML: pyyaml (http://pyyaml.org/)
* binary plist: biplist (https://bitbucket.org/wooster/biplist)

Optional
--------

* HTTP Digest authentication: python3-digest (https://bitbucket.org/akoha/python-digest/)


Why Tastypie?
=============

There are other API frameworks out there for Django. You need to
assess the options available and decide for yourself. That said, here are some
common reasons for tastypie.

* You need an API that is RESTful and uses HTTP well.
* You want to support deep relations.
* You DON'T want to have to write your own serializer to make the output right.
* You want an API framework that has little magic, very flexible and maps well to
  the problem domain.
* You want/need XML serialization that is treated equally to JSON (and YAML is
  there too).


Reference Material
==================

* https://django-tastypie.readthedocs.io/en/latest/
* https://github.com/django-tastypie/django-tastypie/tree/master/tests/basic shows
  basic usage of tastypie
* http://en.wikipedia.org/wiki/REST
* http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
* http://www.ietf.org/rfc/rfc2616.txt
* http://jacobian.org/writing/rest-worst-practices/


Getting Help
============

There are two primary ways of getting help.

1. Go to `StackOverflow`_ and post a question with the ``tastypie`` tag.
2. We have an IRC channel (`#tastypie on irc.freenode.net`_) to get help,
   bounce an idea by us, or generally shoot the breeze.

.. _`StackOverflow`: https://stackoverflow.com/questions/tagged/tastypie
.. _#tastypie on irc.freenode.net: irc://irc.freenode.net/tastypie


Running The Tests
=================

The easiest way to get setup to run Tastypie's tests looks like::

  $ git clone https://github.com/django-tastypie/django-tastypie.git
  $ cd django-tastypie
  $ virtualenv env
  $ . env/bin/activate
  $ ./env/bin/pip install -U -r requirements.txt

Then running the tests is as simple as::

  # From the same directory as above:
  $ ./env/bin/pip install -U -r tests/requirements.txt
  $ ./env/bin/pip install tox
  $ tox

Tastypie is maintained with all tests passing at all times for released
dependencies. (At times tests may fail with development versions of Django.
These will be noted as allowed failures in the ``.travis.yml`` file.) If you
find a failure, please `report it`_ along with the versions of the installed
software.

.. _`report it`: https://github.com/django-tastypie/django-tastypie/issues
