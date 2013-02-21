===============
django-tastypie
===============

Creating delicious APIs for Django apps since 2010.

Currently in beta (v0.9.13) but being used actively in production on several
sites.


Requirements
============

Required
--------

* Python 2.6+
* Django 1.3+
* mimeparse 0.1.3+ (http://code.google.com/p/mimeparse/)

  * Older versions will work, but their behavior on JSON/JSONP is a touch wonky.

* dateutil (http://labix.org/python-dateutil) >= 1.5, < 2.0

Optional
--------

* python_digest (https://bitbucket.org/akoha/python-digest/)
* lxml (http://lxml.de/) if using the XML serializer
* pyyaml (http://pyyaml.org/) if using the YAML serializer
* biplist (http://explorapp.com/biplist/) if using the binary plist serializer


What's It Look Like?
====================

A basic example looks like::

    # myapp/api.py
    # ============
    from tastypie.resources import ModelResource
    from myapp.models import Entry


    class EntryResource(ModelResource):
        class Meta:
            queryset = Entry.objects.all()


    # urls.py
    # =======
    from django.conf.urls.defaults import *
    from tastypie.api import Api
    from myapp.api import EntryResource

    v1_api = Api(api_name='v1')
    v1_api.register(EntryResource())

    urlpatterns = patterns('',
        # The normal jazz here then...
        (r'^api/', include(v1_api.urls)),
    )

That gets you a fully working, read-write API for the ``Entry`` model that
supports all CRUD operations in a RESTful way. JSON/XML/YAML support is already
there, and it's easy to add related data/authentication/caching.

You can find more in the documentation at
http://django-tastypie.readthedocs.org/.


Why Tastypie?
=============

There are other, better known API frameworks out there for Django. You need to
assess the options available and decide for yourself. That said, here are some
common reasons for tastypie.

* You need an API that is RESTful and uses HTTP well.
* You want to support deep relations.
* You DON'T want to have to write your own serializer to make the output right.
* You want an API framework that has little magic, very flexible and maps well to
  the problem domain.
* You want/need XML serialization that is treated equally to JSON (and YAML is
  there too).
* You want to support my perceived NIH syndrome, which is less about NIH and more
  about trying to help out friends/coworkers.


Reference Material
==================

* http://github.com/toastdriven/django-tastypie/tree/master/tests/basic shows
  basic usage of tastypie
* http://en.wikipedia.org/wiki/REST
* http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
* http://www.ietf.org/rfc/rfc2616.txt
* http://jacobian.org/writing/rest-worst-practices/


Commercial Support
==================

If you're using Tastypie in a commercial environment, paid support is available
from `Toast Driven`_. Services offered include:

* Advice/help with setup
* Implementation in your project
* Bugfixes in Tastypie itself
* Features in Tastypie itself

If you're interested, please contact Daniel Lindsley (daniel@toastdriven.com).

.. _`Toast Driven`: http://toastdriven.com/
