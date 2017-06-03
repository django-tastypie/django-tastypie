.. _ref-cookbook:

=================
Tastypie Cookbook
=================

Creating a Full OAuth 2.0 API
-----------------------------

It is common to use django to provision OAuth 2.0 tokens for users and then
have Tasty Pie use these tokens to authenticate users to the API. `Follow this tutorial <http://ianalexandr.com/blog/building-a-true-oauth-20-api-with-django-and-tasty-pie.html>`_ and `use this custom authentication class <https://github.com/ianalexander/django-oauth2-tastypie>`_ to enable
OAuth 2.0 authentication with Tasty Pie.

.. testsetup::

    import os
    import django
    from django.core.management import call_command

    os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
    django.setup()
    call_command('migrate', verbosity=0)

.. testcode::

    # api.py
    from tastypie import fields
    from tastypie.authorization import DjangoAuthorization
    from tastypie.resources import ModelResource, Resource
    from myapp.models import Poll, Choice
    from authentication import OAuth20Authentication


    class ChoiceResource(ModelResource):
        class Meta:
            queryset = Choice.objects.all()
            resource_name = 'choice'
            authorization = DjangoAuthorization()
            authentication = OAuth20Authentication()


    class PollResource(ModelResource):
        choices = fields.ToManyField(ChoiceResource, 'choice_set', full=True)

        class Meta:
            queryset = Poll.objects.all()
            resource_name = 'poll'
            authorization = DjangoAuthorization()
            authentication = OAuth20Authentication()

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Adding Custom Values
--------------------

You might encounter cases where you wish to include additional data in a
response which is not obtained from a field or method on your model. You can
easily extend the :meth:`~tastypie.resources.Resource.dehydrate` method to
provide additional values:

.. testcode::

    from myapp.models import MyModel


    class MyModelResource(Resource):
        class Meta:
            queryset = MyModel.objects.all()

        def dehydrate(self, bundle):
            bundle.data['custom_field'] = "Whatever you want"
            return bundle

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...


Per-Request Alterations To The Queryset
---------------------------------------

A common pattern is needing to limit a queryset by something that changes
per-request, for instance the date/time. You can accomplish this by lightly
modifying ``get_object_list``:

.. testcode::

    from django.utils import timezone
    from myapp.models import MyModel


    class MyModelResource(ModelResource):
        class Meta:
            queryset = MyModel.objects.all()

        def get_object_list(self, request):
            return super(MyModelResource, self).get_object_list(request).filter(start_date__gte=timezone.now())

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...


Using Your ``Resource`` In Regular Views
----------------------------------------

In addition to using your resource classes to power the API, you can also use
them to write other parts of your application, such as your views. For
instance, if you wanted to encode user information in the page for some
Javascript's use, you could do the following. In this case, ``user_json`` will
not include a valid ``resource_uri``:

.. testcode::

    # views.py
    from django.shortcuts import render_to_response
    from myapp.api.resources import UserResource


    def user_detail(request, username):
        res = UserResource()
        request_bundle = res.build_bundle(request=request)
        user = res.obj_get(request_bundle, username=username)

        # Other things get prepped to go into the context then...

        user_bundle = res.build_bundle(request=request, obj=user)
        user_json = res.serialize(None, res.full_dehydrate(user_bundle), "application/json")

        return render_to_response("myapp/user_detail.html", {
            # Other things here.
            "user_json": user_json,
        })

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

To include a valid ``resource_uri``, the resource must be associated
with an ``tastypie.Api`` instance, as below:

.. testcode::

    # urls.py
    from tastypie.api import Api
    from myapp.api.resources import UserResource


    my_api = Api(api_name='v1')
    my_api.register(UserResource())

    # views.py
    from myapp.urls import my_api


    def user_detail(request, username):
        res = my_api.canonical_resource_for('user')
        # continue as above...

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Alternatively, to get a valid ``resource_uri`` you may pass in the ``api_name``
parameter directly to the Resource:

.. testcode::

    # views.py
    from django.shortcuts import render_to_response
    from myapp.api.resources import UserResource


    def user_detail(request, username):
        res = UserResource(api_name='v1')
        # continue as above...

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Example of getting a list of users:

.. testcode::

    def user_list(request):
        res = UserResource()
        request_bundle = res.build_bundle(request=request)
        queryset = res.obj_get_list(request_bundle)

        bundles = []
        for obj in queryset:
            bundle = res.build_bundle(obj=obj, request=request)
            bundles.append(res.full_dehydrate(bundle, for_list=True))

        list_json = res.serialize(None, bundles, "application/json")

        return render_to_response('myapp/user_list.html', {
            # Other things here.
            "list_json": list_json,
        })

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Then in template you could convert JSON into JavaScript object::

    <script>
        var json = "{{ list_json|escapejs }}";
        var users = JSON.parse(json);
    </script>


Using Non-PK Data For Your URLs
-------------------------------

By convention, ``ModelResource``\s usually expose the detail endpoints utilizing
the primary key of the ``Model`` they represent. However, this is not a strict
requirement. Each URL can take other named URLconf parameters that can be used
for the lookup.

For example, if you want to expose ``User`` resources by username, you can do
something like the following:

.. testcode::

    # myapp/api/resources.py
    from django.conf.urls import url
    from django.contrib.auth.models import User


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            detail_uri_name = 'username'

        def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<username>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

The added URLconf matches before the standard URLconf included by default &
matches on the username provided in the URL.

Another alternative approach is to override the ``dispatch`` method:

.. testcode::

    # myapp/api/resources.py
    from myapp.models import MyModel

    class MyModelResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user')

        class Meta:
            queryset = MyModel.objects.all()
            resource_name = 'mymodel'

        def dispatch(self, request_type, request, **kwargs):
            username = kwargs.pop('username')
            kwargs['user'] = get_object_or_404(User, username=username)
            return super(MyModelResource, self).dispatch(request_type, request, **kwargs)

    # urls.py
    from django.conf.urls import url, include

    mymodel_resource = MyModelResource()

    urlpatterns = [
        # The normal jazz here, then...
        url(r'^api/(?P<username>\w+)/', include(mymodel_resource.urls)),
    ]

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...


Nested Resources
----------------

You can also do "nested resources" (resources within another related resource)
by lightly overriding the ``prepend_urls`` method & adding on a new method to
handle the children:

.. testcode::

    class ChildResource(ModelResource):
        pass

    from tastypie.utils import trailing_slash

    class ParentResource(ModelResource):
        children = fields.ToManyField(ChildResource, 'children')

        def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/children%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_children'), name="api_get_children"),
            ]

        def get_children(self, request, **kwargs):
            try:
                bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
                obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
            except ObjectDoesNotExist:
                return HttpGone()
            except MultipleObjectsReturned:
                return HttpMultipleChoices("More than one resource is found at this URI.")

            child_resource = ChildResource()
            return child_resource.get_list(request, parent_id=obj.pk)

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...


Adding Search Functionality
---------------------------

Another common request is being able to integrate search functionality. This
approach uses Haystack_, though you could hook it up to any search technology.
We leave the CRUD methods of the resource alone, choosing to add a new endpoint
at ``/api/v1/notes/search/``::

    from django.conf.urls import url, include
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

Alternately, in this recipe we leverage the Haystack ``SearchQuerySet`` API to expose documents from our search index themselves, vice piggy-backing on another resource for search functionality.::

    import operator
    
    from haystack.query import SearchQuerySet, SQ

    from tastypie import fields
    from tastypie.bundle import Bundle
    from tastypie.resources import Resource, ResourceOptions, DeclarativeMetaclass


    class SearchOptions(ResourceOptions):
        # One of the great strengths of Haystack is its extensibility. We have
        # subclassed many of Haystack's internal classes, including a subclass
        # of SearchQuerySet. I did not want to be locked in to using Haystack's
        # built-in SearchQuerySet nor its SQ object in this module, so I put in
        # the ``query_object`` attribute on the metaclass.
        resource_name = 'search'
        object_class = SearchQuerySet
        query_object = SQ
        index_fields = []
        # Override document_uid_field with whatever field in your index
        # you use to uniquely identify a single document. This value will be
        # used wherever the ModelResource references the ``pk`` kwarg.
        document_uid_field = 'id'
        lookup_sep = ','


    class SearchDeclarativeMetaclass(DeclarativeMetaclass):
        def __new__(cls, name, bases, attrs):
            new_class = super(SearchDeclarativeMetaclass, cls)\
                .__new__(cls, name, bases, attrs)
            opts = getattr(new_class, 'Meta', None)
            new_class._meta = SearchOptions(opts)
            include_fields = getattr(new_class._meta, 'fields', [])
            excludes = getattr(new_class._meta, 'excludes', [])
            field_names = new_class.base_fields.keys()

            for field_name in field_names:
                if field_name == 'resource_uri':
                    continue
                if field_name in new_class.declared_fields:
                    continue
                if len(include_fields) and not field_name in include_fields:
                    del(new_class.base_fields[field_name])
                if len(excludes) and field_name in excludes:
                    del(new_class.base_fields[field_name])

            if getattr(new_class._meta, 'include_absolute_url', True):
                if not 'absolute_url' in new_class.base_fields:
                    new_class.base_fields['absolute_url'] = fields.CharField(
                        attribute='get_absolute_url', readonly=True)
            elif 'absolute_url' in new_class.base_fields and not 'absolute_url' in attrs:
                del(new_class.base_fields['absolute_url'])

            return new_class


    class SearchResource(Resource):
        """
        Blueprint for implementing an HTTP API to access documents in a
        search engine via Haystack. The design of the class adds some
        additional configuration overhead (i.e. a handful of metaclass
        fields) in exchange for flexibility & portability.

        To implement this class in your own application, you will need to:
        1. Define which fields to return in your results;
        2. Override index_fields in the metaclass to limit or expand which
           fields consumers can access from your index via the API;
        3. Override document_uid_field in the metaclass to specify which
           field in the index is used to uniquely identify individual
           documents;
        4. Additionally, you will override query_object and object_class to
           utilize any subclasses you may be using in your project.

        """
        __metaclass__ = SearchDeclarativeMetaclass

        def apply_filters(self, request, applicable_filters):
            objects = self.get_object_list(request)

            if applicable_filters:
                return objects.filter(applicable_filters)
            else:
                return objects

        def build_filters(self, filters=None):
            """
            Create a single SQ filter from querystring parameters that
            correspond to SearchIndex fields that have been "registered" in
            the ``self._meta.index_fields``.

            Default behavior is to ``OR`` terms for the same parameter, and
            ``AND`` between parameters. For example:

            ``?format=json&state_exact=Indiana,Illinois&company_exact=IBM``

            would yield an SQ expressing the following logic:

            ``q=state_exact:(Indiana OR Illinois) AND company_exact:IBM``

            Any querystring parameters that are not registered in
            self._meta.index_fields and are not consumed elsewhere in the
            response operation will be ignored.

            """
            terms = []

            if filters is None:
                filters = {}

            for param, value in filters.items():

                if param not in self._meta.index_fields:
                    continue

                tokens = value.split(self._meta.lookup_sep)
                field_queries = []

                for token in tokens:

                    if token:
                        field_queries.append(self._meta.query_object((param,
                                                                      token)))

                terms.append(reduce(operator.or_,
                                    filter(lambda x: x, field_queries)))

            if terms:
                return reduce(operator.and_, filter(lambda x: x, terms))
            else:
                return terms

        def get_resource_uri(self, bundle_or_obj):
            """
            Generate direct link to individual document in our datastore.

            """
            kwargs = {
                'resource_name': self._meta.resource_name
            }
            uid = self._meta.document_uid_field

            if isinstance(bundle_or_obj, Bundle):
                kwargs['pk'] = getattr(bundle_or_obj.obj, uid, '')
            else:
                kwargs['pk'] = getattr(bundle_or_obj, uid, '')

            if self._meta.api_name is not None:
                kwargs['api_name'] = self._meta.api_name

            return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

        def get_object_list(self, request):
            """
            A Haystack-specific implementation of ``get_object_list``.

            Returns a SearchQuerySet that may have been limited by other
            filter/narrow/etc. operations.

            """
            return self._meta.object_class()._clone()

        def obj_get_list(self, request=None, **kwargs):
            filters = {}

            if hasattr(request, 'GET'):
                filters = request.GET.copy()

            filters.update(kwargs)
            applicable_filters = self.build_filters(filters=filters)
            return self.apply_filters(request, applicable_filters)

        def obj_get(self, request=None, **kwargs):
            """
            Fetch a single document from the datastore according to whatever
            unique identifier is available for that document in the
            SearchIndex.

            """
            # Don't let the use of 'pk' here and throughout confuse you.
            # Think of it as a metaphor standing for "whatever field there
            # is in your SearchIndex that uniquely identifies a single
            # document."
            doc_uid = kwargs.get('pk')
            uid_field = self._meta.document_uid_field
            sqs = self.get_object_list(request)

            if doc_uid:
                sqs = sqs.filter(self._meta.query_object((uid_field, doc_uid)))

                if sqs:
                    return sqs[0]
                else:
                    return sqs
                        


.. _Haystack: http://haystacksearch.org/


Creating per-user resources
---------------------------

One might want to create an API which will require every user to authenticate
and every user will be working only with objects associated with them. Let's see
how to implement it for two basic operations: listing and creation of an object.

For listing we want to list only objects for which 'user' field matches
'request.user'. This could be done by applying a filter in the
``authorized_read_list`` method of your resource.

For creating we'd have to wrap ``obj_create`` method of ``ModelResource``. Then the
resulting code will look something like:

.. testcode::

    # myapp/api/resources.py
    from tastypie.authentication import ApiKeyAuthentication
    from tastypie.authorization import Authorization


    class MyModelResource(ModelResource):
        class Meta:
            queryset = MyModel.objects.all()
            resource_name = 'mymodel'
            list_allowed_methods = ['get', 'post']
            authentication = ApiKeyAuthentication()
            authorization = Authorization()

        def obj_create(self, bundle, **kwargs):
            return super(MyModelResource, self).obj_create(bundle, user=bundle.request.user)

        def authorized_read_list(self, object_list, bundle):
            return object_list.filter(user=bundle.request.user)

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

camelCase JSON Serialization
----------------------------

The convention in the world of Javascript has standardized on camelCase,
where Tastypie uses underscore syntax, which can lead to "ugly" looking
code in Javascript. You can create a custom serializer that emits
values in camelCase instead:

.. testcode::

    import re
    import json
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

            return json.dumps(camelized_data, sort_keys=True)

        def from_json(self, content):
            # Changes camelCase names to underscore_separated names to go from javascript convention to python convention
            data = json.loads(content)

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

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Pretty-printed JSON Serialization
---------------------------------

By default, Tastypie outputs JSON with no indentation or newlines (equivalent to calling
:py:func:`json.dumps` with *indent* set to ``None``). You can override this
behavior in a custom serializer:

.. testcode::

    import json
    from django.core.serializers.json import DjangoJSONEncoder
    from tastypie.serializers import Serializer

    class PrettyJSONSerializer(Serializer):
        json_indent = 2

        def to_json(self, data, options=None):
            options = options or {}
            data = self.to_simple(data, options)
            return json.dumps(data, cls=DjangoJSONEncoder,
                    sort_keys=True, ensure_ascii=False, indent=self.json_indent)

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Determining format via URL
--------------------------

Sometimes it's required to allow selecting the response format by
specifying it in the API URL, for example ``/api/v1/users.json`` instead
of ``/api/v1/users/?format=json``. The following snippet allows that kind
of syntax additional to the default URL scheme:

.. testcode::

    # myapp/api/resources.py

    from django.contrib.auth.models import User
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

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

Adding to the Django Admin
--------------------------

If you're using the django admin and ApiKeyAuthentication, you may want to see
or edit ApiKeys next to users. To do this, you need to unregister the built-in
UserAdmin, alter the inlines, and re-register it. This could go in any of your
admin.py files. You may also want to register ApiAccess and ApiKey models on
their own.:

.. testcode::

    from django.contrib import admin
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.models import User

    from tastypie.admin import ApiKeyInline


    class UserModelAdmin(UserAdmin):
        inlines = UserAdmin.inlines + [ApiKeyInline]


    admin.site.unregister(User)
    admin.site.register(User, UserModelAdmin)

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...


Using ``SessionAuthentication``
-------------------------------

If your users are logged into the site & you want Javascript to be able to
access the API (assuming jQuery), the first thing to do is setup
``SessionAuthentication``:

.. testcode::

    from django.contrib.auth.models import User
    from tastypie.authentication import SessionAuthentication
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            resource_name = 'users'
            queryset = User.objects.all()
            authentication = SessionAuthentication()

.. testoutput::
   :options: +NORMALIZE_WHITESPACE
   :hide:

    ...

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
