===============
django-tastypie
===============

Creating delicious APIs for Django apps since 2010.


Requirements
============

* Python 2.4+
* Django 1.0+
* mimeparse (http://code.google.com/p/mimeparse/)
* dateutil (http://labix.org/python-dateutil)
* lxml (http://codespeak.net/lxml/) if using the XML serializer
* pyyaml (http://pyyaml.org/) if using the YAML serializer
* uuid (present in 2.5+, downloadable from http://pypi.python.org/pypi/uuid/) if using the ``ApiKey`` authentication


Why tastypie?
=============

You want an API framework that has less magic, very flexible and maps well to
the problem domain.

You want an API framework that doesn't involve overriding a 115+ line
``__call__`` function to assert some control over your API.

You want to support my perceived NIH syndrome, which is less about NIH and more
about trying to help out friends/coworkers.


Reference Material
==================

* http://github.com/toastdriven/django-tastypie/tree/master/tests/basic shows
  basic usage of tastypie
* http://en.wikipedia.org/wiki/REST
* http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
* http://www.ietf.org/rfc/rfc2616.txt
* http://jacobian.org/writing/rest-worst-practices/

:author: Daniel Lindsley
:date: 2010/06/19
