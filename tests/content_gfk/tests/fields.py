from __future__ import with_statement

from django.test import TestCase
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.bundle import Bundle
from content_gfk.models import Note, Quote, Rating, Definition
from content_gfk.api.resources import NoteResource, DefinitionResource, \
    QuoteResource, RatingResource


class ContentTypeFieldTestCase(TestCase):

    def test_init(self):
        # Test that you have to use a dict some other resources
        with self.assertRaises(ValueError):
            GenericForeignKeyField(((Note, NoteResource)), 'nofield')

        # Test that you must register some other resources
        with self.assertRaises(ValueError):
            GenericForeignKeyField({}, 'nofield')

        # Test that the resources you raise must be models
        with self.assertRaises(ValueError):
            GenericForeignKeyField({NoteResource: Note}, 'nofield')

    def test_get_related_resource(self):
        gfk_field = GenericForeignKeyField({
            Note: NoteResource,
            Quote: QuoteResource
        }, 'nofield')

        definition_1 = Definition.objects.create(
            word='toast',
            content="Cook or brown (food, esp. bread or cheese)"
        )

        # Test that you can not link to a model that does not have a resource
        with self.assertRaises(TypeError):
            gfk_field.get_related_resource(definition_1)

        note_1 = Note.objects.create(
            title='All aboard the rest train',
            content='Sometimes it is just better to lorem ipsum'
        )

        self.assertTrue(isinstance(gfk_field.get_related_resource(note_1), NoteResource))

    def test_resource_from_uri(self):
        note_2 = Note.objects.create(
            title='Generic and such',
            content='Sometimes it is to lorem ipsum'
        )

        gfk_field = GenericForeignKeyField({
            Note: NoteResource,
            Quote: QuoteResource
        }, 'nofield')

        self.assertEqual(
            gfk_field.resource_from_uri(
                gfk_field.to_class(),
                '/api/v1/notes/%s/' % note_2.pk
            ).obj,
            note_2
        )

    def test_build_related_resource(self):
        gfk_field = GenericForeignKeyField({
            Note: NoteResource,
            Quote: QuoteResource
        }, 'nofield')

        quote_1 = Quote.objects.create(
            byline='Issac Kelly',
            content='To ipsum or not to ipsum, that is the cliche'
        )
        qr = QuoteResource()
        qr.build_bundle(obj=quote_1)

        bundle = gfk_field.build_related_resource(
            '/api/v1/quotes/%s/' % quote_1.pk
        )

        # Test that the GFK field builds the same as the QuoteResource
        self.assertEqual(bundle.obj, quote_1)
