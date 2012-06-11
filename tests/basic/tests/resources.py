from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.fields import ToOneField, ToManyField
from tastypie.resources import ModelResource
from basic.api.resources import SlugBasedNoteResource
from basic.models import Note, AnnotatedNote


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


class NoteModelResourceTestCase(TestCase):
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

        try:
            ilur.notes.to_class()
            self.fail("to_class on InvalidLazyUserResource should fail!")
        except ImportError:
            pass

        try:
            nplur.notes.to_class()
            self.fail("to_class on NoPathLazyUserResource should fail!")
        except ImportError:
            pass

        to_class = lur.notes.to_class()
        self.assertTrue(isinstance(to_class, NoteResource))
        # This is important, as without passing on the ``api_name``, URL
        # reversals will fail. Fakes the instance as ``None``, since for
        # testing purposes, we don't care.
        related = lur.notes.get_related_resource(None)
        self.assertEqual(related._meta.api_name, 'foo')


class AnnotatedNoteModelResourceTestCase(TestCase):
    def test_one_to_one_regression(self):
        # Make sure bits don't completely blow up if the related model
        # is gone.
        n1 = Note.objects.get(pk=1)

        resource_1 = NoteWithAnnotationsResource()
        n1_bundle = resource_1.build_bundle(obj=n1)
        dehydrated = resource_1.full_dehydrate(n1_bundle)


class DetailURIKwargsResourceTestCase(TestCase):
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
        n1 = Note.objects.get(pk=1)

        resource = SlugBasedNoteResource()
        self.assertEqual(resource.detail_uri_kwargs(n1), {
            'slug': 'first-post',
        })

    def test_correct_slug_detail_uri_bundle(self):
        n1 = Note.objects.get(pk=1)

        resource = SlugBasedNoteResource()
        n1_bundle = resource.build_bundle(obj=n1)
        self.assertEqual(resource.detail_uri_kwargs(n1_bundle), {
            'slug': 'first-post',
        })

