from __future__ import unicode_literals
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound
from django.core.urlresolvers import resolve, Resolver404, get_script_prefix


class ContentTypeResourceMixin(ModelResource):
    content_type = fields.CharField()

    def dehydrate_content_type(self, bundle):
        return bundle.obj.__class__.__name__.lower()


class GenericResource(ModelResource):
    """
    Provides a stand-in resource for GFK relations.
    """
    def __init__(self, resources, *args, **kwargs):
        self.resources = resources
        self.resource_mapping = dict((r._meta.resource_name, r)
                                     for r in resources.values())
        self.model_mapping = dict((v._meta.resource_name, k)
                                  for k, v in resources.iteritems())
        return super(GenericResource, self).__init__(*args, **kwargs)

    def get_via_uri(self, uri, request=None):
        """
        This pulls apart the salient bits of the URI and populates the
        resource via a ``obj_get``.

        Optionally accepts a ``request``.

        If you need custom behavior based on other portions of the URI,
        simply override this method.
        """
        prefix = get_script_prefix()
        chomped_uri = uri

        if prefix and chomped_uri.startswith(prefix):
            chomped_uri = chomped_uri[len(prefix)-1:]

        try:
            view, args, kwargs = resolve(chomped_uri)
            resource_name = kwargs['resource_name']
            self.resource_mapping[resource_name]
        except (Resolver404, KeyError):
            raise NotFound("The URL provided '%s' was not a link to a valid resource." % uri)

    def get_resource_uri(self, bundle, *args, **kwargs):
            Resource = self.resources[bundle.obj.__class__]
            return Resource().get_resource_uri(bundle, *args, **kwargs)

    def full_dehydrate(self, bundle, for_list=False):
        Resource = self.resources[bundle.obj.__class__]

        class _ProxyResource(ContentTypeResourceMixin, Resource):
            def get_resource_uri(self, *args, **kwargs):
                return Resource().get_resource_uri(*args, **kwargs)

            class Meta(Resource.Meta):
                pass
        return _ProxyResource().full_dehydrate(bundle, for_list)

    def full_hydrate(self, bundle):
        Resource = self.resource_mapping[bundle.data['content_type']]
        return Resource().full_hydrate(bundle)

    def save(self, bundle, skip_errors=False):
        Resource = self.resource_mapping[bundle.data['content_type']]
        return Resource().save(bundle, skip_errors)
