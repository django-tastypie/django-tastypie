from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from pull769.models import Simple, Related


class SimpleResource(ModelResource):
    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Simple.objects.all()
        resource_name = 'simple'


class RelatedResource(ModelResource):
    simple = fields.ForeignKey(SimpleResource, 'simple', full=True, null=False, blank=False)

    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Related.objects.all()
        resource_name = 'related'
