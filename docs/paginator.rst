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
