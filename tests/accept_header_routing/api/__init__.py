from django.conf.urls.defaults import *
from tastypie.api import Api, AcceptHeaderRouter
from accept_header_routing.api.resources import (NoteResource, UserResource,
    BusinessResource, OrganizationResource, NoteResource2)

api_router = AcceptHeaderRouter()


api_v1 = Api(api_name='v1')
api_v1.register(NoteResource())
api_v1.register(UserResource())
api_v1.register(OrganizationResource())
api_router.register(api_v1)

api_v2 = Api(api_name='v2')
api_v2.register(NoteResource2())
api_v2.register(UserResource())
api_v2.register(BusinessResource())
api_router.register(api_v2, default=True)
