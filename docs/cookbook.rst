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

You can also do "nested resources" (resources within another related resource)
by lightly overriding the ``dispatch`` method in a similar way::

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
