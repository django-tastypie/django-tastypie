# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.http import HttpRequest
from tastypie.fields import ToOneField, ToManyField
from tastypie.resources import ModelResource
from basic.api.resources import SlugBasedNoteResource
from basic.models import Note, AnnotatedNote, SlugBasedNote
from testcases import TestCaseWithFixture


class InvalidLazyUserResource(ModelResource):
    notes = ToManyField('basic.api.resources.FooResource', 'notes')

    class Meta:
        queryset = User.objects.all()


class NoPathLazyUserResource(ModelResource):
    notes = ToManyField('FooResource', 'notes')

    class Meta:
        queryset = User.objects.all()


class LazyUserResource(ModelResource):
    notes = ToManyField('basic.tests.resources.NoteResource', 'notes')

    class Meta:
        queryset = User.objects.all()
        api_name = 'foo'


class NoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.all()


class AnnotatedNoteResource(ModelResource):
    class Meta:
        queryset = AnnotatedNote.objects.all()


class NoteWithAnnotationsResource(ModelResource):
    annotated = ToOneField(AnnotatedNoteResource, 'annotated', null=True)

    class Meta:
        queryset = Note.objects.all()


class NoteModelResourceTestCase(TestCaseWithFixture):
    def test_init(self):
        resource_1 = NoteResource()
        self.assertEqual(len(resource_1.fields), 8)
        self.assertNotEqual(resource_1._meta.queryset, None)
        self.assertEqual(resource_1._meta.resource_name, 'note')

        # TextFields should have ``default=''`` to match Django's behavior,
        # even though that's not what is on the field proper.
        self.assertEqual(resource_1.fields['content'].default, '')

    def test_lazy_relations(self):
        ilur = InvalidLazyUserResource()
        nplur = NoPathLazyUserResource()
        lur = LazyUserResource()

        self.assertEqual(ilur.notes.to, 'basic.api.resources.FooResource')
        self.assertEqual(nplur.notes.to, 'FooResource')
        self.assertEqual(lur.notes.to, 'basic.tests.resources.NoteResource')

        with self.assertRaises(ImportError):
            ilur.notes.to_class()

        with self.assertRaises(ImportError):
            nplur.notes.to_class()

        to_class = lur.notes.to_class()
        self.assertTrue(isinstance(to_class, NoteResource))
        # This is important, as without passing on the ``api_name``, URL
        # reversals will fail. Fakes the instance as ``None``, since for
        # testing purposes, we don't care.
        related = lur.notes.get_related_resource(None)
        self.assertEqual(related._meta.api_name, 'foo')


class AnnotatedNoteModelResourceTestCase(TestCaseWithFixture):
    def test_one_to_one_regression(self):
        # Make sure bits don't completely blow up if the related model
        # is gone.
        n1 = Note.objects.get(pk=1)

        resource_1 = NoteWithAnnotationsResource()
        n1_bundle = resource_1.build_bundle(obj=n1)
        resource_1.full_dehydrate(n1_bundle)


class DetailURIKwargsResourceTestCase(TestCaseWithFixture):
    def test_correct_detail_uri_model(self):
        n1 = Note.objects.get(pk=1)

        resource = NoteWithAnnotationsResource()
        self.assertEqual(resource.detail_uri_kwargs(n1), {
            'pk': 1,
        })

    def test_correct_detail_uri_bundle(self):
        n1 = Note.objects.get(pk=1)

        resource = NoteWithAnnotationsResource()
        n1_bundle = resource.build_bundle(obj=n1)
        self.assertEqual(resource.detail_uri_kwargs(n1_bundle), {
            'pk': 1,
        })

    def test_correct_slug_detail_uri_model(self):
        n1 = SlugBasedNote.objects.get(pk='first-post')

        resource = SlugBasedNoteResource()
        self.assertEqual(resource.detail_uri_kwargs(n1), {
            'slug': 'first-post',
        })

    def test_correct_slug_detail_uri_bundle(self):
        n1 = SlugBasedNote.objects.get(pk='first-post')

        resource = SlugBasedNoteResource()
        n1_bundle = resource.build_bundle(obj=n1)
        self.assertEqual(resource.detail_uri_kwargs(n1_bundle), {
            'slug': 'first-post',
        })


class SlugBasedResourceTestCase(TestCaseWithFixture):
    def setUp(self):
        super(SlugBasedResourceTestCase, self).setUp()
        self.n1 = SlugBasedNote.objects.get(pk='first-post')
        self.request = HttpRequest()
        self.request.method = 'PUT'
        self.resource = SlugBasedNoteResource()
        self.n1_bundle = self.resource.build_bundle(obj=self.n1)

    def test_bundle_unique_field(self):
        self.assertEqual(self.resource.get_bundle_detail_data(self.n1_bundle), u'first-post')

    def test_obj_update(self):
        bundle = self.resource.build_bundle(obj=self.n1, data={
            'title': 'Foo!',
        })
        updated_bundle = self.resource.obj_update(bundle, slug='first-post')
        self.assertEqual(updated_bundle.obj.slug, 'first-post')
        self.assertEqual(updated_bundle.obj.title, 'Foo!')

        # Again, without the PK this time.
        self.n1.slug = None
        bundle = self.resource.build_bundle(obj=self.n1, data={
            'title': 'Bar!',
        })
        updated_bundle_2 = self.resource.obj_update(bundle, slug='first-post')
        self.assertEqual(updated_bundle_2.obj.slug, 'first-post')
        self.assertEqual(updated_bundle_2.obj.title, 'Bar!')

    def test_update_in_place(self):
        new_data = {
            'slug': u'foo',
            'title': u'Foo!',
        }
        new_bundle = self.resource.update_in_place(self.request, self.n1_bundle, new_data)
        # Check for updated data.
        self.assertEqual(new_bundle.obj.title, u'Foo!')
        self.assertEqual(new_bundle.obj.slug, u'foo')
        # Make sure it looked up the right instance, even though we didn't
        # hand it a PK...
        self.assertEqual(new_bundle.obj.pk, self.n1_bundle.obj.pk)

    def test_rollback(self):
        bundles = [
            self.n1_bundle
        ]
        self.resource.rollback(bundles)

        # Make sure it's gone.
        self.assertRaises(SlugBasedNote.DoesNotExist, SlugBasedNote.objects.get, pk='first-post')


class BundleTestCase(TestCaseWithFixture):
    def test_bundle_repr(self):
        # __repr__ should return string type (str in PY2 or unicode in PY3)
        n = Note.objects.get(pk=1)

        resource = NoteWithAnnotationsResource()
        n1_bundle = resource.build_bundle(obj=n)
        self.assertTrue(isinstance(repr(n1_bundle), str))

        data_dict = {
            u'∆ключ∆': 1,
            'привет©®': 2
        }
        n2_bundle = resource.build_bundle(obj=n, data=data_dict)
        self.assertTrue(isinstance(repr(n2_bundle), str))
