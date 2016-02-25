.. _ref-paginator:

=========
Paginator
=========

Similar to Django's ``Paginator``, Tastypie includes a ``Paginator`` object
which limits result sets down to sane amounts for passing to the client.

This is used in place of Django's ``Paginator`` due to the way pagination
works. ``limit`` & ``offset`` (tastypie) are used in place of ``page``
(Django) so none of the page-related calculations are necessary.

This implementation also provides additional details like the
``total_count`` of resources seen and convenience links to the
``previous``/``next`` pages of data as available.

Usage
=====

Using this class is simple, but slightly different than the other classes used
by Tastypie. Like the others, you provide the ``Paginator`` (or your own
subclass) as a ``Meta`` option to the ``Resource`` in question. **Unlike** the
others, you provide the class, *NOT* an instance. For example::

    from django.contrib.auth.models import User
    from tastypie.paginator import Paginator
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            paginator_class = Paginator


.. warning::

    The default paginator contains the ``total_count`` value, which shows how
    many objects are in the underlying object list.

    Obtaining this data from the database may be inefficient, especially
    with large datasets, and unfiltered API requests.

    See http://wiki.postgresql.org/wiki/Slow_Counting and
    http://www.wikivs.com/wiki/MySQL_vs_PostgreSQL#COUNT.28.2A.29
    for reference, on why this may be a problem when using PostgreSQL and
    MySQL's InnoDB engine.

    Here's an :ref:`example solution <paginator-estimated-count>` to this
    problem.


Implementing Your Own Paginator
===============================

Adding other features to a paginator usually consists of overriding one of
the built-in methods. For instance, adding a page number to the output
might look like::

    from tastypie.paginator import Paginator


    class PageNumberPaginator(Paginator):
        def page(self):
            output = super(PageNumberPaginator, self).page()
            output['page_number'] = int(self.offset / self.limit) + 1
            return output

Another common request is to alter the structure Tastypie uses in the
list view. Here's an example of renaming::

    from tastypie.paginator import Paginator


    class BlogEntryPaginator(Paginator):
        def page(self):
            output = super(BlogEntryPaginator, self).page()

            # First keep a reference.
            output['pagination'] = output['meta']
            output['entries'] = output['objects']

            # Now nuke the original keys.
            del output['meta']
            del output['objects']

            return output

.. _paginator-estimated-count:

``Estimated count instead of total count``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Here's an example, of how you can omit ``total_count`` from the resource,
and instead add an ``estimated_count`` for efficiency. See the warning above
for details::

    import json

    from django.db import connection

    from tastypie.paginator import Paginator


    class EstimatedCountPaginator(Paginator):

        def get_next(self, limit, offset, count):
            # The parent method needs an int which is higher than "limit + offset"
            # to return a url. Setting it to an unreasonably large value, so that
            # the parent method will always return the url.
            count = 2 ** 64
            return super(EstimatedCountPaginator, self).get_next(limit, offset, count)

        def get_count(self):
            return None

        def get_estimated_count(self):
            """Get the estimated count by using the database query planner."""
            # If you do not have PostgreSQL as your DB backend, alter this method
            # accordingly.
            return self._get_postgres_estimated_count()

        def _get_postgres_estimated_count(self):

            # This method only works with postgres >= 9.0.
            # If you need postgres vesrions less than 9.0, remove "(format json)"
            # below and parse the text explain output.

            def _get_postgres_version():
                # Due to django connections being lazy, we need a cursor to make
                # sure the connection.connection attribute is not None.
                connection.cursor()
                return connection.connection.server_version

            try:
                if _get_postgres_version() < 90000:
                    return
            except AttributeError:
                return

            cursor = connection.cursor()
            query = self.objects.all().query

            # Remove limit and offset from the query, and extract sql and params.
            query.low_mark = None
            query.high_mark = None
            query, params = self.objects.query.sql_with_params()

            # Fetch the estimated rowcount from EXPLAIN json output.
            query = 'explain (format json) %s' % query
            cursor.execute(query, params)
            explain = cursor.fetchone()[0]
            # Older psycopg2 versions do not convert json automatically.
            if isinstance(explain, basestring):
                explain = json.loads(explain)
            rows = explain[0]['Plan']['Plan Rows']
            return rows

        def page(self):
            data = super(EstimatedCountPaginator, self).page()
            data['meta']['estimated_count'] = self.get_estimated_count()
            return data
