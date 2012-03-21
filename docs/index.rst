Welcome to Tastypie!
====================

Tastypie is an webservice API framework for Django. It provides a convenient,
yet powerful and highly customizable, abstraction for creating REST-style
interfaces.

.. toctree::
   :maxdepth: 2

   tutorial
   interacting
   settings
   non_orm_data_sources
   tools

   resources
   bundles
   api
   fields
   caching
   validation
   authentication_authorization
   serialization
   throttling
   paginator
   geodjango

   cookbook
   debugging
   who_uses
   contributing


Getting Help
============

There are two primary ways of getting help. We have a `mailing list`_ hosted at
Google (http://groups.google.com/group/django-tastypie/) and an IRC channel
(`#tastypie on irc.freenode.net`_) to get help, want to bounce idea or
generally shoot the breeze.

.. _`mailing list`: http://groups.google.com/group/django-tastypie/
.. _#tastypie on irc.freenode.net: irc://irc.freenode.net/tastypie


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

    from tastypie.api import Api
    from my_app.api.resources import MyModelResource

    v1_api = Api(api_name='v1')
    v1_api.register(MyModelResource())

    urlpatterns = patterns('',
      # ...more URLconf bits here...
      # Then add:
      (r'^api/', include(v1_api.urls)),
    )

5. Hit http://localhost:8000/api/v1/?format=json in your browser!


Requirements
============

Tastypie requires the following modules. If you use Pip_, you can install
the necessary bits via the included ``requirements.txt``:

Required
--------

* Python 2.5+
* Django 1.2+
* mimeparse 0.1.3+ (http://code.google.com/p/mimeparse/)

  * Older versions will work, but their behavior on JSON/JSONP is a touch wonky.

* dateutil (http://labix.org/python-dateutil) >= 1.5, < 2.0

Optional
--------

* python_digest (https://bitbucket.org/akoha/python-digest/)
* lxml (http://lxml.de/) if using the XML serializer
* pyyaml (http://pyyaml.org/) if using the YAML serializer
* biplist (http://explorapp.com/biplist/) if using the binary plist serializer

.. _Pip: http://pip.openplans.org/


Running The Tests
=================

The easiest way to get setup to run Tastypie's tests looks like::

  $ git clone https://github.com/toastdriven/django-tastypie.git
  $ cd django-tastypie
  $ virtualenv env
  $ . env/bin/activate
  $ ./env/bin/pip install -U -r requirements.txt

Then running the tests is as simple as::

  # From the same directory as above:
  $ cd tests
  $ ./run_all_test.sh

Tastypie is maintained with all tests passing at all times. If you find a
failure, please `report it`_ along with the versions of the installed software.

.. _`report it`: https://github.com/toastdriven/django-tastypie/issues
