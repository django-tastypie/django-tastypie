from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User, Permission
from core.models import Note
from tastypie.authorization import Authorization, ReadOnlyAuthorization, DjangoAuthorization
from tastypie.exceptions import Unauthorized
from tastypie import fields
from tastypie.resources import Resource, ModelResource


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

    def test_no_rules(self):
        request = HttpRequest()
        resource = NoRulesNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.read_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'POST'
        self.assertRaises(NotImplementedError, auth.create_list, resource.get_object_list(bundle.request), bundle)
        self.assertTrue(auth.create_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.update_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.delete_detail(resource.get_object_list(bundle.request)[0], bundle))

    def test_read_only(self):
        request = HttpRequest()
        resource = ReadOnlyNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.read_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.create_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.update_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.delete_detail, resource.get_object_list(bundle.request)[0], bundle)


class DjangoAuthorizationTestCase(TestCase):
    fixtures = ['note_testdata']

    def setUp(self):
        super(DjangoAuthorizationTestCase, self).setUp()
        self.add = Permission.objects.get_by_natural_key('add_note', 'core', 'note')
        self.change = Permission.objects.get_by_natural_key('change_note', 'core', 'note')
        self.delete = Permission.objects.get_by_natural_key('delete_note', 'core', 'note')
        self.user = User.objects.all()[0]
        self.user.user_permissions.clear()

    def test_no_perms(self):
        # sanity check: user has no permissions
        self.assertFalse(self.user.get_all_permissions())

        request = HttpRequest()
        request.user = self.user
        # with no permissions, api is read-only
        resource = DjangoNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.read_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.create_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.update_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.delete_detail, resource.get_object_list(bundle.request)[0], bundle)

    def test_add_perm(self):
        request = HttpRequest()
        request.user = self.user

        # give add permission
        request.user.user_permissions.add(self.add)

        request = HttpRequest()
        request.user = self.user
        resource = DjangoNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.read_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.create_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.update_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.delete_detail, resource.get_object_list(bundle.request)[0], bundle)

    def test_change_perm(self):
        request = HttpRequest()
        request.user = self.user

        # give change permission
        request.user.user_permissions.add(self.change)

        resource = DjangoNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.read_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.create_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.update_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.delete_detail, resource.get_object_list(bundle.request)[0], bundle)

    def test_delete_perm(self):
        request = HttpRequest()
        request.user = self.user

        # give delete permission
        request.user.user_permissions.add(self.delete)

        resource = DjangoNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.read_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.create_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 0)
        self.assertRaises(Unauthorized, auth.update_detail, resource.get_object_list(bundle.request)[0], bundle)

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.delete_detail(resource.get_object_list(bundle.request)[0], bundle))

    def test_all(self):
        request = HttpRequest()
        request.user = self.user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        resource = DjangoNoteResource()
        auth = resource._meta.authorization
        bundle = resource.build_bundle(request=request)

        bundle.request.method = 'GET'
        self.assertEqual(len(auth.read_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.read_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'POST'
        self.assertEqual(len(auth.create_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.create_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'PUT'
        self.assertEqual(len(auth.update_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.update_detail(resource.get_object_list(bundle.request)[0], bundle))

        bundle.request.method = 'DELETE'
        self.assertEqual(len(auth.delete_list(resource.get_object_list(bundle.request), bundle)), 4)
        self.assertTrue(auth.delete_detail(resource.get_object_list(bundle.request)[0], bundle))
