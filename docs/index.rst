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
   
   resources
   api
   fields
   caching
   validation
   authentication_authorization
   serialization
   throttling
   
   cookbook
   debugging
   who_uses


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

* Python 2.4+
* Django 1.0+
* mimeparse 0.1.3+ (http://code.google.com/p/mimeparse/)

  * Older versions will work, but their behavior on JSON/JSONP is a touch wonky.

* dateutil (http://labix.org/python-dateutil)
* lxml (http://codespeak.net/lxml/) if using the XML serializer
* pyyaml (http://pyyaml.org/) if using the YAML serializer

If you choose to use Python 2.4, be warned that you will also need to grab the
following modules:

* uuid (present in 2.5+, downloadable from http://pypi.python.org/pypi/uuid/) if using the ``ApiKey`` authentication

.. _Pip: http://pip.openplans.org/
