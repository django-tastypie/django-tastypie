.. _namespaces:

==========
Namespaces
==========

For various reasons you might want to deploy your API under a namespaced URL path. To support that tastypie includes ``NamespacedApi`` and ``NamespacedModelResource``.

A sample definition of your API in this case would be something like::

    from django.urls.conf import re_path, include
    from tastypie.api import NamespacedApi
    from my_application.api.resources import NamespacedUserResource

    api = NamespacedApi(api_name='v1', urlconf_namespace='special')
    api.register(NamespacedUserResource())

    urlpatterns = [
        re_path(r'^api/', include(api.urls, namespace='special')),
    ]

And your model resource::

    from django.contrib.auth.models import User
    from tastypie.resources import NamespacedModelResource
    from tastypie.authorization import Authorization

    class NamespacedUserResource(NamespacedModelResource):
        class Meta:
            resource_name = 'users'
            queryset = User.objects.all()
            authorization = Authorization()
