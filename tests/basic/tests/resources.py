from django.test import TestCase
from tastypie.resources import ModelResource
from basic.models import Note


class NoteResource(ModelResource):
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
