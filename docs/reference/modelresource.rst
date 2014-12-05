.. _model-resource-reference:

ModelResource Reference
***********************

.. note::
   See also the reference for the :ref:`Resource <resource-reference>` class
   since ``ModelResource`` inherits from it, including all of its attributes and
   methods.


``ModelResource`` Methods
=========================

A subclass of ``Resource`` designed to work with Django's ``Models``.

This class will introspect a given ``Model`` and build a field list based
on the fields found on the model (excluding relational fields).

Given that it is aware of Django's ORM, it also handles the CRUD data
operations of the resource.

``should_skip_field``
---------------------

.. method:: ModelResource.should_skip_field(cls, field)

*Class method*

Given a Django model field, return if it should be included in the
contributed ApiFields.

``api_field_from_django_field``
-------------------------------

.. method:: ModelResource.api_field_from_django_field(cls, f, default=CharField)

*Class method*

Returns the field type that would likely be associated with each
Django type.

``get_fields``
--------------

.. method:: ModelResource.get_fields(cls, fields=None, excludes=None)

*Class method*

Given any explicit fields to include and fields to exclude, add
additional fields based on the associated model.

``check_filtering``
-------------------

.. method:: ModelResource.check_filtering(self, field_name, filter_type='exact', filter_bits=None)

Given a field name, a optional filter type and an optional list of
additional relations, determine if a field can be filtered on.

If a filter does not meet the needed conditions, it should raise an
``InvalidFilterError``.

If the filter meets the conditions, a list of attribute names (not
field names) will be returned.

``build_filters``
-----------------

.. method:: ModelResource.build_filters(self, filters=None)

Given a dictionary of filters, create the necessary ORM-level filters.

Keys should be resource fields, **NOT** model fields.

Valid values are either a list of Django filter types (i.e.
``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
``ALL_WITH_RELATIONS`` constant.

At the declarative level::

    filtering = {
        'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        'resource_field_name_3': ALL,
        'resource_field_name_4': ALL_WITH_RELATIONS,
        ...
    }

Accepts the filters as a dict. ``None`` by default, meaning no filters.

``apply_sorting``
-----------------

.. method:: ModelResource.apply_sorting(self, obj_list, options=None)

Given a dictionary of options, apply some ORM-level sorting to the
provided ``QuerySet``.

Looks for the ``order_by`` key and handles either ascending (just the
field name) or descending (the field name with a ``-`` in front).

The field name should be the resource field, **NOT** model field.

``apply_filters``
-----------------

.. method:: ModelResource.apply_filters(self, request, applicable_filters)

An ORM-specific implementation of ``apply_filters``.

The default simply applies the ``applicable_filters`` as ``**kwargs``,
but should make it possible to do more advanced things.

``get_object_list``
-------------------

.. method:: ModelResource.get_object_list(self, request)

A ORM-specific implementation of ``get_object_list``.

Returns a ``QuerySet`` that may have been limited by other overrides.

``obj_get_list``
----------------

.. method:: ModelResource.obj_get_list(self, filters=None, **kwargs)

A ORM-specific implementation of ``obj_get_list``.

Takes an optional ``filters`` dictionary, which can be used to narrow
the query.

``obj_get``
-----------

.. method:: ModelResource.obj_get(self, **kwargs)

A ORM-specific implementation of ``obj_get``.

Takes optional ``kwargs``, which are used to narrow the query to find
the instance.

``obj_create``
--------------

.. method:: ModelResource.obj_create(self, bundle, **kwargs)

A ORM-specific implementation of ``obj_create``.

``obj_update``
--------------

.. method:: ModelResource.obj_update(self, bundle, **kwargs)

A ORM-specific implementation of ``obj_update``.

``obj_delete_list``
-------------------

.. method:: ModelResource.obj_delete_list(self, **kwargs)

A ORM-specific implementation of ``obj_delete_list``.

Takes optional ``kwargs``, which can be used to narrow the query.

``obj_delete_list_for_update``
------------------------------

.. method:: ModelResource.obj_delete_list_for_update(self, **kwargs)

A ORM-specific implementation of ``obj_delete_list_for_update``.

Takes optional ``kwargs``, which can be used to narrow the query.

``obj_delete``
--------------

.. method:: ModelResource.obj_delete(self, **kwargs)

A ORM-specific implementation of ``obj_delete``.

Takes optional ``kwargs``, which are used to narrow the query to find
the instance.

``rollback``
------------

.. method:: ModelResource.rollback(self, bundles)

A ORM-specific implementation of ``rollback``.

Given the list of bundles, delete all models pertaining to those
bundles.

``save_related``
----------------

.. method:: ModelResource.save_related(self, bundle)

Handles the saving of related non-M2M data.

Calling assigning ``child.parent = parent`` & then calling
``Child.save`` isn't good enough to make sure the ``parent``
is saved.

To get around this, we go through all our related fields &
call ``save`` on them if they have related, non-M2M data.
M2M data is handled by the ``ModelResource.save_m2m`` method.

``save_m2m``
------------

.. method:: ModelResource.save_m2m(self, bundle)

Handles the saving of related M2M data.

Due to the way Django works, the M2M data must be handled after the
main instance, which is why this isn't a part of the main ``save`` bits.

Currently slightly inefficient in that it will clear out the whole
relation and recreate the related data as needed.

``get_resource_uri``
--------------------

.. method:: ModelResource.get_resource_uri(self, bundle_or_obj)

Handles generating a resource URI for a single resource.

Uses the model's ``pk`` in order to create the URI.
