from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User, Permission
from core.models import Note
from tastypie.authorization import Authorization, ReadOnlyAuthorization, DjangoAuthorization
from tastypie import fields
from tastypie.resources import Resource, ModelResource

authorization_detail_map = {
    'GET': 'read_detail',
    'HEAD': 'read_detail',
    'POST': 'create_detail',
    'PUT': 'update_detail',
    'PATCH': 'update_detail',
    'DELETE': 'delete_detail',
}

authorization_list_map = {
    'GET': 'read_list',
    'HEAD': 'read_list',
    'POST': 'create_list',
    'PUT': 'update_list',
    'PATCH': 'update_list',
    'DELETE': 'delete_list',
}

class NoRulesNoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authorization = Authorization()


class ReadOnlyNoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authorization = ReadOnlyAuthorization()


class DjangoNoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authorization = DjangoAuthorization()


class NotAModel(object):
    name = 'Foo'


class NotAModelResource(Resource):
    name = fields.CharField(attribute='name')

    class Meta:
        resource_name = 'notamodel'
        object_class = NotAModel
        authorization = DjangoAuthorization()


class AuthorizationTestCase(TestCase):
    fixtures = ['note_testdata']
    def setUp(self):
        self.no_rules_note_resource = NoRulesNoteResource()
        self.read_only_note_resource = ReadOnlyNoteResource()

    def test_no_rules_details(self):
        request = HttpRequest()
        obj_list = self.no_rules_note_resource.get_object_list(request)
        #any object will do
        obj = obj_list[0]
        bundle = self.no_rules_note_resource.build_bundle(request=request, obj=obj)
        for method in ('GET', 'POST', 'PUT', 'DELETE'):
            request.method = method
            self.assertTrue(getattr(self.no_rules_note_resource._meta.authorization, \
                authorization_detail_map[method])(obj_list, bundle))

    def test_no_rules_list_post(self):
        request = HttpRequest()
        bundle = self.no_rules_note_resource.build_bundle(request=request)
        obj_list = self.no_rules_note_resource.get_object_list(request)

        self.assertRaises(NotImplementedError, self.no_rules_note_resource._meta.authorization.create_list, \
            obj_list, bundle)

    def test_no_rules_list(self):
        request = HttpRequest()
        bundle = self.no_rules_note_resource.build_bundle(request=request)
        for method in ('GET', 'PUT', 'DELETE'):
            request.method = method

            #get a fresh list of objects each time
            obj_list = self.no_rules_note_resource.get_object_list(request)
            authorized_obj_list = getattr(self.no_rules_note_resource._meta.authorization, \
                authorization_list_map[method])(obj_list, bundle)

            self.assertTrue(authorized_obj_list is obj_list)

    def test_read_only_details(self):
        request = HttpRequest()
        obj_list = self.read_only_note_resource.get_object_list(request)
        #any object will do
        obj = obj_list[0]
        bundle = self.read_only_note_resource.build_bundle(request=request, obj=obj)


        request.method = 'GET'
        self.assertTrue(self.read_only_note_resource._meta.authorization.read_detail(obj_list, bundle))

        for method in ('POST', 'PUT', 'DELETE'):
            request.method = method
            self.assertFalse(getattr(self.read_only_note_resource._meta.authorization, \
                authorization_detail_map[method])(obj_list, bundle))


    def test_read_only_list_get(self):
        request = HttpRequest()
        bundle = self.read_only_note_resource.build_bundle(request=request)
        request.method = 'GET'

        #get a fresh list of objects each time
        obj_list = self.read_only_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.read_only_note_resource._meta.authorization, \
            authorization_list_map['GET'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)

    def test_read_only_list(self):
        request = HttpRequest()
        bundle = self.read_only_note_resource.build_bundle(request=request)
        for method in ('POST', 'PUT', 'DELETE'):
            request.method = method

            #get a fresh list of objects each time
            obj_list = self.read_only_note_resource.get_object_list(request)
            authorized_obj_list = getattr(self.read_only_note_resource._meta.authorization, \
                authorization_list_map[method])(obj_list, bundle)

            self.assertEqual(len(authorized_obj_list), 0)


class DjangoAuthorizationTestCase(TestCase):
    fixtures = ['note_testdata']

    def setUp(self):
        self.add = Permission.objects.get_by_natural_key('add_note', 'core', 'note')
        self.change = Permission.objects.get_by_natural_key('change_note', 'core', 'note')
        self.delete = Permission.objects.get_by_natural_key('delete_note', 'core', 'note')
        self.user = User.objects.all()[0]
        self.user.user_permissions.clear()
        self.django_note_resource = DjangoNoteResource()
        self.not_a_model_resource = NotAModelResource()

    def test_no_perms_details(self):
        # sanity check: user has no permissions
        self.assertFalse(self.user.get_all_permissions())

        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        #any object will do
        obj = obj_list[0]
        bundle = self.django_note_resource.build_bundle(request=request, obj=obj)


        request.method = 'GET'
        self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
            authorization_detail_map['GET'])(obj_list, bundle))

        for method in ('POST', 'PUT', 'DELETE'):
            request.method = method
            self.assertFalse(getattr(self.django_note_resource._meta.authorization, \
                authorization_detail_map[method])(obj_list, bundle))

    def test_no_perms_list_get(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)
        request.method = 'GET'

        #get a fresh list of objects each time
        obj_list = self.django_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
            authorization_list_map['GET'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)

    def test_no_perms_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)

        for method in ('POST', 'PUT', 'DELETE'):
            request.method = method

            #get a fresh list of objects each time
            obj_list = self.django_note_resource.get_object_list(request)
            authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
                authorization_list_map[method])(obj_list, bundle)

            self.assertEqual(len(authorized_obj_list), 0)

    def test_add_perm_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        bundle = self.django_note_resource.build_bundle(request=request)

        # give add permission
        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
            authorization_detail_map['POST'])(obj_list, bundle))

    def test_add_perm_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        #get a fresh list of objects each time
        obj_list = self.django_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
            authorization_list_map['POST'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)


    def test_add_perm_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        bundle = self.django_note_resource.build_bundle(request=request)

        # give add permission
        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
            authorization_detail_map['POST'])(obj_list, bundle))

    def test_add_perm_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        #get a fresh list of objects each time
        obj_list = self.django_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
            authorization_list_map['POST'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)

    def test_change_perm_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        bundle = self.django_note_resource.build_bundle(request=request)

        # give add permission
        request.user.user_permissions.add(self.change)
        request.method = 'PUT'

        self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
            authorization_detail_map['PUT'])(obj_list, bundle))

    def test_change_perm_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.change)
        request.method = 'PUT'

        #get a fresh list of objects each time
        obj_list = self.django_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
            authorization_list_map['PUT'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)


    def test_change_delete_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        bundle = self.django_note_resource.build_bundle(request=request)

        # give add permission
        request.user.user_permissions.add(self.delete)
        request.method = 'DELETE'

        self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
            authorization_detail_map['DELETE'])(obj_list, bundle))

    def test_change_delete_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.delete)
        request.method = 'DELETE'

        #get a fresh list of objects each time
        obj_list = self.django_note_resource.get_object_list(request)
        authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
            authorization_list_map['DELETE'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)

    def test_all_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = self.django_note_resource.get_object_list(request)
        bundle = self.django_note_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)


        #not sure what to do about 'OPTIONS'
        for method in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):
            request.method = method
            self.assertTrue(getattr(self.django_note_resource._meta.authorization, \
                authorization_detail_map[method])(obj_list, bundle))

    def test_all_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.django_note_resource.build_bundle(request=request)


        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)


        #not sure what to do about 'OPTIONS'
        for method in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):

            request.method = method

            #get a fresh list of objects each time
            obj_list = self.django_note_resource.get_object_list(request)
            authorized_obj_list = getattr(self.django_note_resource._meta.authorization, \
                authorization_list_map[method])(obj_list, bundle)

            self.assertTrue(authorized_obj_list is obj_list)

    def test_not_a_model_post_perm_details(self):
        request = HttpRequest()
        request.user = self.user
        obj_list = []
        bundle = self.not_a_model_resource.build_bundle(request=request)

        # give add permission
        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        self.assertTrue(getattr(self.not_a_model_resource._meta.authorization, \
            authorization_detail_map['POST'])(obj_list, bundle))

    def test_not_a_model_post_perm_list(self):
        request = HttpRequest()
        request.user = self.user
        bundle = self.not_a_model_resource.build_bundle(request=request)

        request.user.user_permissions.add(self.add)
        request.method = 'POST'

        #get a fresh list of objects each time
        obj_list = []
        authorized_obj_list = getattr(self.not_a_model_resource._meta.authorization, \
            authorization_list_map['POST'])(obj_list, bundle)

        self.assertTrue(authorized_obj_list is obj_list)

    #Not sure if this is a valid use case anymore
    def test_unrecognized_method(self):
        request = HttpRequest()
        request.user = self.user

        # Check a non-existent HTTP method.
        request.method = 'EXPLODE'
        self.assertFalse(DjangoNoteResource()._meta.authorization.is_authorized(request))
