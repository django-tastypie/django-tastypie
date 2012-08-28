from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound
from django.core.urlresolvers import resolve, Resolver404, get_script_prefix


class GenericResource(ModelResource):
    """
    Provides a stand-in resource for GFK relations.
    """

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
        except Resolver404:
            raise NotFound("The URL provided '%s' was not a link to a valid resource." % uri)

        parent_resource = view.func_closure[0].cell_contents.func_closure[0].cell_contents
        return parent_resource.obj_get(**self.remove_api_resource_names(kwargs))

