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


Per-Request Alterations To The Queryset
---------------------------------------

A common pattern is needing to limit a queryset by something that changes
per-request, for instance the date/time. You can accomplish this by lightly
modifying ``get_object_list``::

    from tastypie.utils import now

    class MyResource(ModelResource):
        class Meta:
            queryset = MyObject.objects.all()

        def get_object_list(self, request):
            return super(MyResource, self).get_object_list(request).filter(start_date__gte=now)


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
        user = ur.obj_get(username=username)

        # Other things get prepped to go into the context then...

        ur_bundle = ur.build_bundle(obj=user, request=request)
        return render_to_response('myapp/user_detail.html', {
            # Other things here.
            "user_json": ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'),
        })


Using Non-PK Data For Your URLs
-------------------------------

By convention, ``ModelResource``\s usually expose the detail endpoints utilizing
the primary key of the ``Model`` they represent. However, this is not a strict
requirement. Each URL can take other named URLconf parameters that can be used
for the lookup.

For example, if you want to expose ``User`` resources by username, you can do
something like the following::

    # myapp/api/resources.py
    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()

        def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<username>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

The added URLconf matches before the standard URLconf included by default &
matches on the username provided in the URL.


Nested Resources
----------------

You can also do "nested resources" (resources within another related resource)
by lightly overriding the ``prepend_urls`` method & adding on a new method to
handle the children::

    class ParentResource(ModelResource):
        children = fields.ToManyField(ChildResource, 'children')

        def prepend_urls(self):
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

        def prepend_urls(self):
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
                bundle = self.build_bundle(obj=result.object, request=request)
                bundle = self.full_dehydrate(bundle)
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
and every user will be working only with objects associated with them. Let's see
how to implement it for two basic operations: listing and creation of an object.

For listing we want to list only objects for which 'user' field matches
'request.user'. This could be done by applying a filter in the ``apply_authorization_limits``
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

camelCase JSON Serialization
----------------------------

The convention in the world of Javascript has standardized on camelCase,
where Tastypie uses underscore syntax, which can lead to "ugly" looking
code in Javascript. You can create a custom serializer that emits
values in camelCase instead::

    from tastypie.serializers import Serializer

    class CamelCaseJSONSerializer(Serializer):
        formats = ['json']
        content_types = {
            'json': 'application/json',
        }

        def to_json(self, data, options=None):
            # Changes underscore_separated names to camelCase names to go from python convention to javacsript convention
            data = self.to_simple(data, options)

            def underscoreToCamel(match):
                return match.group()[0] + match.group()[2].upper()

            def camelize(data):
                if isinstance(data, dict):
                    new_dict = {}
                    for key, value in data.items():
                        new_key = re.sub(r"[a-z]_[a-z]", underscoreToCamel, key)
                        new_dict[new_key] = camelize(value)
                    return new_dict
                if isinstance(data, (list, tuple)):
                    for i in range(len(data)):
                        data[i] = camelize(data[i])
                    return data
                return data

            camelized_data = camelize(data)

            return simplejson.dumps(camelized_data, sort_keys=True)

        def from_json(self, content):
            # Changes camelCase names to underscore_separated names to go from javascript convention to python convention
            data = simplejson.loads(content)

            def camelToUnderscore(match):
                return match.group()[0] + "_" + match.group()[1].lower()

            def underscorize(data):
                if isinstance(data, dict):
                    new_dict = {}
                    for key, value in data.items():
                        new_key = re.sub(r"[a-z][A-Z]", camelToUnderscore, key)
                        new_dict[new_key] = underscorize(value)
                    return new_dict
                if isinstance(data, (list, tuple)):
                    for i in range(len(data)):
                        data[i] = underscorize(data[i])
                    return data
                return data

        underscored_data = underscorize(data)

        return underscored_data

Pretty-printed JSON Serialization
---------------------------------

By default, Tastypie outputs JSON with no indentation or newlines (equivalent to calling
:py:func:`json.dumps` with *indent* set to ``None``). You can override this
behavior in a custom serializer::

    from django.core.serializers import json
    from django.utils import simplejson
    from tastypie.serializers import Serializer

    class PrettyJSONSerializer(Serializer):
        json_indent = 2

        def to_json(self, data, options=None):
            options = options or {}
            data = self.to_simple(data, options)
            return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                    sort_keys=True, ensure_ascii=False, indent=self.json_indent)

Determining format via URL
--------------------------

Sometimes it's required to allow selecting the response format by
specifying it in the API URL, for example ``/api/v1/users.json`` instead
of ``/api/v1/users/?format=json``. The following snippet allows that kind
of syntax additional to the default URL scheme::

    # myapp/api/resources.py

    # Piggy-back on internal csrf_exempt existence handling
    from tastypie.resources import csrf_exempt

    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()

        def prepend_urls(self):
            """
            Returns a URL scheme based on the default scheme to specify
            the response format as a file extension, e.g. /api/v1/users.json
            """
            return [
                url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
                url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
                url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
                url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

        def determine_format(self, request):
            """
            Used to determine the desired format from the request.format
            attribute.
            """
            if (hasattr(request, 'format') and
                    request.format in self._meta.serializer.formats):
                return self._meta.serializer.get_mime_for_format(request.format)
            return super(UserResource, self).determine_format(request)

        def wrap_view(self, view):
            @csrf_exempt
            def wrapper(request, *args, **kwargs):
                request.format = kwargs.pop('format', None)
                wrapped_view = super(UserResource, self).wrap_view(view)
                return wrapped_view(request, *args, **kwargs)
            return wrapper

Adding to the Django Admin
--------------------------

If you're using the django admin and ApiKeyAuthentication, you may want to see
or edit ApiKeys next to users. To do this, you need to unregister the built-in
UserAdmin, alter the inlines, and re-register it. This could go in any of your
admin.py files. You may also want to register ApiAccess and ApiKey models on
their own.::

    from tastypie.admin import ApiKeyInline
    from tastypie.models import ApiAccess, ApiKey
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.models import User

    admin.site.register(ApiKey)
    admin.site.register(ApiAccess)

    class UserModelAdmin(UserAdmin):
        inlines = UserAdmin.inlines + [ApiKeyInline]

    admin.site.unregister(User)
    admin.site.register(User,UserModelAdmin)


Using ``SessionAuthentication``
-------------------------------

If your users are logged into the site & you want Javascript to be able to
access the API (assuming jQuery), the first thing to do is setup
``SessionAuthentication``::

    from django.contrib.auth.models import User
    from tastypie.authentication import SessionAuthentication
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            resource_name = 'users'
            queryset = User.objects.all()
            authentication = SessionAuthentication()

Then you'd build a template like::

    <html>
        <head>
            <title></title>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
            <script type="text/javascript">
                $(document).ready(function() {
                    // We use ``.ajax`` here due to the overrides.
                    $.ajax({
                        // Substitute in your API endpoint here.
                        url: '/api/v1/users/',
                        contentType: 'application/json',
                        // The ``X-CSRFToken`` evidently can't be set in the
                        // ``headers`` option, so force it here.
                        // This method requires jQuery 1.5+.
                        beforeSend: function(jqXHR, settings) {
                            // Pull the token out of the DOM.
                            jqXHR.setRequestHeader('X-CSRFToken', $('input[name=csrfmiddlewaretoken]').val());
                        },
                        success: function(data, textStatus, jqXHR) {
                            // Your processing of the data here.
                            console.log(data);
                        }
                    });
                });
            </script>
        </head>
        <body>
            <!-- Include the CSRF token in the body of the HTML -->
            {% csrf_token %}
        </body>
    </html>

There are other ways to make this function, with other libraries or other
techniques for supplying the token (see
https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax for an
alternative). This is simply a starting point for getting things working.
