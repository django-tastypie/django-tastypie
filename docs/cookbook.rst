.. _ref-cookbook:

=================
Tastypie Cookbook
=================


Adding Custom Values
--------------------

You might encounter cases where you wish to include additional data in a
response which is not obtained from a field or method on your model. You can
easily extend the :meth:`~tastypie.resources.Resource.dehydrate` method to
provide additional values::

    class MyModelResource(Resource):
        class Meta:
            qs = MyModel.objects.all()

        def dehydrate(self, bundle):
            bundle.data['custom_field'] = "Whatever you want"
            return bundle


Using Your ``Resource`` In Regular Views
----------------------------------------

In addition to using your resource classes to power the API, you can also use
them to write other parts of your application, such as your views. For
instance, if you wanted to encode user information in the page for some
Javascript's use, you could do the following::

    # views.py
    from django.shortcuts import render_to_response
    from myapp.api.resources import UserResource
    
    
    def user_detail(request, username):
        ur = UserResource()
        user = ur.obj_get_detail(username=username)
        
        # Other things get prepped to go into the context then...
        
        return render_to_response('myapp/user_detail.html', {
            # Other things here.
            "user_json": ur.serialize(None, ur.full_dehydrate(obj=user), 'application/json'),
        })


Using Non-PK Data For Your URLs
-------------------------------

By convention, ``ModelResource``s usually expose the detail endpoints utilizing
the primary key of the ``Model`` they represent. However, this is not a strict
requirement. Each URL can take other named URLconf parameters that can be used
for the lookup.

For example, if you want to expose ``User`` resources by username, you can do
something like the following::

    # myapp/api/resources.py
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
        
        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<username>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

The added URLconf matches before the standard URLconf included by default &
matches on the username provided in the URL.


Nested Resources
----------------

You can also do "nested resources" (resources within another related resource)
by lightly overriding the ``override_urls`` method & adding on a new method to
handle the children::

    class ParentResource(ModelResource):
        children = fields.ToManyField(ChildResource, 'children')
        
        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/children%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_children'), name="api_get_children"),
            ]
        
        def get_children(self, request, **kwargs):
            try:
                obj = self.cached_obj_get(request=request, **self.remove_api_resource_names(kwargs))
            except ObjectDoesNotExist:
                return HttpGone()
            except MultipleObjectsReturned:
                return HttpMultipleChoices("More than one resource is found at this URI.")
            
            child_resource = ChildResource()
            return child_resource.get_detail(request, parent_id=obj.pk)

Another alternative approach is to override the ``dispatch`` method::

    # myapp/api/resources.py
    class EntryResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user')
        
        class Meta:
            queryset = Entry.objects.all()
            resource_name = 'entry'
        
        def dispatch(self, request_type, request, **kwargs):
            username = kwargs.pop('username')
            kwargs['user'] = get_object_or_404(User, username=username)
            return super(EntryResource, self).dispatch(request_type, request, **kwargs)
    
    # urls.py
    from django.conf.urls.defaults import *
    from myapp.api import EntryResource

    entry_resource = EntryResource()

    urlpatterns = patterns('',
        # The normal jazz here, then...
        (r'^api/(?P<username>\w+)/', include(entry_resource.urls)),
    )


Adding Search Functionality
---------------------------

Another common request is being able to integrate search functionality. This
approach uses Haystack_, though you could hook it up to any search technology.
We leave the CRUD methods of the resource alone, choosing to add a new endpoint
at ``/api/v1/notes/search/``::

    from django.conf.urls.defaults import *
    from django.core.paginator import Paginator, InvalidPage
    from django.http import Http404
    from haystack.query import SearchQuerySet
    from tastypie.resources import ModelResource
    from tastypie.utils import trailing_slash
    from notes.models import Note
    
    
    class NoteResource(ModelResource):
        class Meta:
            queryset = Note.objects.all()
            resource_name = 'notes'
        
        def override_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            ]
        
        def get_search(self, request, **kwargs):
            self.method_check(request, allowed=['get'])
            self.is_authenticated(request)
            self.throttle_check(request)
            
            # Do the query.
            sqs = SearchQuerySet().models(Note).load_all().auto_query(request.GET.get('q', ''))
            paginator = Paginator(sqs, 20)
            
            try:
                page = paginator.page(int(request.GET.get('page', 1)))
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")
            
            objects = []
            
            for result in page.object_list:
                bundle = self.full_dehydrate(result.object)
                objects.append(bundle)
            
            object_list = {
                'objects': objects,
            }
            
            self.log_throttled_access(request)
            return self.create_response(request, object_list)

.. _Haystack: http://haystacksearch.org/


Creating per-user resources
---------------------------

One might want to create an API which will require every user to authenticate
and every user will be working only with objects associated with him. Let's see
how to implement it for two basic operations: listing and creation of an object.

For listing we want to list only objects for which 'user' field matches
'request.user'. This could be done my applying filter in ``apply_authorization_limits``
method of your resource.

For creating we'd have to wrap ``obj_create`` method of ``ModelResource``. Then the
resulting code will look something like::

    # myapp/api/resources.py
    class EnvironmentResource(ModelResource):
        class Meta:
            queryset = Environment.objects.all()
            resource_name = 'environment'
            list_allowed_methods = ['get', 'post']
            authentication = ApiKeyAuthentication()
            authorization = Authorization()
        
        def obj_create(self, bundle, request=None, **kwargs):
            return super(EnvironmentResource, self).obj_create(bundle, request, user=request.user)
        
        def apply_authorization_limits(self, request, object_list):
            return object_list.filter(user=request.user)
