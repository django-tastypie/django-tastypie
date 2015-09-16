from tastypie.authorization import Authorization
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.resources import ModelResource
from content_gfk.models import Note, Quote, Definition, Rating


class DefinitionResource(ModelResource):

    class Meta:
        resource_name = 'definitions'
        queryset = Definition.objects.all()


class NoteResource(ModelResource):

    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.all()


class QuoteResource(ModelResource):

    class Meta:
        resource_name = 'quotes'
        queryset = Quote.objects.all()


class RatingResource(ModelResource):
    content_object = GenericForeignKeyField({
        Note: NoteResource,
        Quote: QuoteResource
    }, 'content_object')

    class Meta:
        resource_name = 'ratings'
        queryset = Rating.objects.all()
        authorization = Authorization()
