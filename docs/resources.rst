.. _ref-filtering_sorting:

=====================
Filtering And Sorting
=====================

Basic Filtering
---------------

:class:`~tastypie.resources.ModelResource` provides a basic Django ORM filter
interface. Simply list the resource fields which you'd like to filter on and
the allowed expression in a `filtering` property of your resource's Meta
class::

    from tastypie.constants import ALL, ALL_WITH_RELATIONS

    class MyResource(ModelResource):
        class Meta:
            filtering = {
                "slug": ('exact', 'startswith',),
                "title": ALL,
            }

Valid filtering values are: Django ORM filters (e.g. ``startswith``,
``exact``, ``lte``, etc. or the ``ALL`` or ``ALL_WITH_RELATIONS`` constants
defined in :mod:`tastypie.constants`.

These filters will be extracted from URL query strings using the same
double-underscore syntax as the Django ORM::

    /api/v1/myresource/?slug=myslug
    /api/v1/myresource/?slug__startswith=test

Advanced Filtering
------------------

If you need to filter things other than ORM resources or wish to apply
additional constraints (e.g. text filtering using `django-haystack
<http://haystacksearch.org>` rather than simple database queries) your
:class:`~tastypie.resources.Resource` may define a custom
:meth:`~tastypie.resource.Resource.build_filters` method which allows you to
filter the queryset before processing a request::

    from haystack.query import SearchQuerySet

    class MyResource(Resource):
        def build_filters(self, filters=None):
            if filters is None:
                filters = {}

            orm_filters = super(MyResource, self).build_filters(filters)

            if "q" in filters:
                sqs = SearchQuerySet().auto_query(filters['q'])

                orm_filters = {"pk__in": [ i.pk for i in sqs ]}

            return orm_filters
