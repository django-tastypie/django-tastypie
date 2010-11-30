from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.fields import ToOneField, ToManyField
from tastypie.resources import ModelResource
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
        
        self.assertTrue(isinstance(lur.notes.to_class(), NoteResource))

class AnnotatedNoteModelResourceTestCase(TestCase):
    def test_one_to_one_regression(self):
        # Make sure bits don't completely blow up if the related model
        # is gone.
        n1 = Note.objects.get(pk=1)
        
        resource_1 = NoteWithAnnotationsResource()
        dehydrated = resource_1.full_dehydrate(n1)
