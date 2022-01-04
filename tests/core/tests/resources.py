# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from collections import OrderedDict
import copy
import datetime
from decimal import Decimal
import json
from mock import patch, Mock
import sys
import time
from unittest import skipIf

import django
from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import FieldError, MultipleObjectsReturned, ObjectDoesNotExist, ImproperlyConfigured
from django.core import mail
from time import mktime
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpRequest, QueryDict, Http404
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import (
    InvalidFilterError, InvalidSortError, ImmediateHttpResponse, BadRequest,
    NotFound, UnsupportedFormat,
    UnsupportedSerializationFormat, UnsupportedDeserializationFormat,
)
from tastypie import fields, http
from tastypie.compat import force_str
from tastypie.paginator import Paginator
from tastypie.resources import (
    ALL, ALL_WITH_RELATIONS, convert_post_to_put, convert_post_to_patch,
    Resource, ModelResource,
)
from tastypie.serializers import Serializer
from tastypie.throttle import CacheThrottle
from tastypie.utils import aware_datetime, make_naive
from tastypie.validation import FormValidation

from core.models import (
    Note, NoteWithEditor, Subject, MediaBit, AutoNowNote, DateRecord, Counter,
    MyDefaultPKModel, MyUUIDModel, MyRelatedUUIDModel, BigAutoNowModel,
)
from core.tests.mocks import MockRequest
from core.utils import adjust_schema, SimpleHandler

User = get_user_model()


class CustomSerializer(Serializer):
    pass


class TestObject(object):
    name = None
    view_count = None
    date_joined = None


class BasicResourceWithDifferentListAndDetailFields(Resource):
    name = fields.CharField(attribute='name', use_in="all")
    view_count = fields.IntegerField(attribute='view_count', default=0, use_in="detail")
    date_joined = fields.DateTimeField(null=True, use_in="list")

    def dehydrate_date_joined(self, bundle):
        if getattr(bundle.obj, 'date_joined', None) is not None:
            return bundle.obj.date_joined

        if bundle.data.get('date_joined') is not None:
            return bundle.data.get('date_joined')

        return aware_datetime(2010, 3, 27, 22, 30, 0)

    def hydrate_date_joined(self, bundle):
        bundle.obj.date_joined = bundle.data['date_joined']
        return bundle

    def obj_get_list(self, bundle, **kwargs):
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = aware_datetime(2010, 3, 30, 9, 0, 0)
        return [test_object_1]

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'basic'


class BasicResourceWithDifferentListAndDetailFieldsCallable(Resource):
    name = fields.CharField(attribute='name', use_in="all")
    view_count = fields.IntegerField(attribute='view_count', default=0, use_in=lambda x: True)
    date_joined = fields.DateTimeField(null=True, use_in=lambda x: False)

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'basic'


class BasicResource(Resource):
    name = fields.CharField(attribute='name', verbose_name="Basic name")
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateTimeField(null=True)

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'basic'
        authorization = Authorization()

    def dehydrate_date_joined(self, bundle):
        if getattr(bundle.obj, 'date_joined', None) is not None:
            return bundle.obj.date_joined

        if bundle.data.get('date_joined') is not None:
            return bundle.data.get('date_joined')

        return aware_datetime(2010, 3, 27, 22, 30, 0)

    def hydrate_date_joined(self, bundle):
        bundle.obj.date_joined = bundle.data['date_joined']
        return bundle

    def get_list(self, request, **kwargs):
        raise NotImplementedError


class AnotherBasicResource(BasicResource):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateField(attribute='created')
    is_active = fields.BooleanField(attribute='is_active', default=True)
    aliases = fields.ListField(attribute='aliases', null=True)
    meta = fields.DictField(attribute='metadata', null=True)
    owed = fields.DecimalField(attribute='money_owed', null=True)

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'anotherbasic'
        authorization = Authorization()

    def dehydrate(self, bundle):
        if hasattr(bundle.obj, 'bar'):
            bundle.data['bar'] = bundle.obj.bar

        bundle.data['aliases'] = ['Mr. Smith', 'John Doe']
        bundle.data['meta'] = {'threat': 'high'}
        bundle.data['owed'] = Decimal('102.57')
        return bundle

    def hydrate(self, bundle):
        if 'bar' in bundle.data:
            bundle.obj.bar = 'O HAI BAR!'

        return bundle


class NoUriBasicResource(BasicResource):
    name = fields.CharField(attribute='name')
    view_count = fields.IntegerField(attribute='view_count', default=0)
    date_joined = fields.DateTimeField(null=True)

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        include_resource_uri = False
        authorization = Authorization()


class NullableNameResource(Resource):
    name = fields.CharField(attribute='name', null=True)

    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'nullable_name'
        authorization = Authorization()


class MangledBasicResource(BasicResource):
    class Meta:
        object_class = TestObject
        detail_uri_name = 'name'
        resource_name = 'mangledbasic'
        authorization = Authorization()

    def alter_list_data_to_serialize(self, request, data_dict):
        if isinstance(data_dict, dict):
            if 'meta' in data_dict:
                # Get rid of the "meta".
                del(data_dict['meta'])
                # Rename the objects.
                data_dict['testobjects'] = copy.copy(data_dict['objects'])
                del(data_dict['objects'])

        return data_dict

    def alter_deserialized_detail_data(self, request, bundle_or_list):
        # Automatically shove in the user.
        if isinstance(bundle_or_list, Bundle):
            # Handle the detail.
            bundle_or_list.data['user'] = request.user
        elif isinstance(bundle_or_list, list):
            # Handle the list.
            for obj_data in bundle_or_list:
                obj_data['user'] = request.user

        return bundle_or_list


class MROBaseFieldResourceA(Resource):
    test = fields.CharField(default='test_a')


class MROBaseFieldResourceB(Resource):
    test = fields.CharField(default='test_b')
    name = fields.CharField(default='Mr. Field')


class MROFieldResource(MROBaseFieldResourceA, MROBaseFieldResourceB):
    pass


class ConvertTestCase(TestCase):
    def test_to_put(self):
        request = HttpRequest()
        request.method = 'PUT'
        # Obviously not the right data, but we just need to make sure it gets
        # removed.
        request._post = 'foo'
        request._files = 'bar'
        request.POST = {
            'test': 'thing'
        }
        # Make Django happy.
        request._read_started = False
        request._raw_post_data = request._body = ''

        modified = convert_post_to_put(request)
        self.assertEqual(modified.method, 'PUT')
        self.assertEqual(len(modified._post), 0)
        self.assertEqual(len(modified._files), 0)
        self.assertEqual(modified.POST, {'test': 'thing'})
        self.assertEqual(modified.PUT, {'test': 'thing'})

    def test_to_patch(self):
        request = HttpRequest()
        request.method = 'PATCH'
        # Obviously not the right data, but we just need to make sure it gets
        # removed.
        request._post = 'foo'
        request._files = 'bar'
        request.POST = {
            'test': 'thing'
        }
        # Make Django happy.
        request._read_started = False
        request._raw_post_data = request._body = ''

        modified = convert_post_to_patch(request)
        self.assertEqual(modified.method, 'PATCH')
        self.assertEqual(len(modified._post), 0)
        self.assertEqual(len(modified._files), 0)
        self.assertEqual(modified.POST, {'test': 'thing'})
        self.assertEqual(modified.PATCH, {'test': 'thing'})


class ResourceTestCase(TestCase):
    def test_deserialize(self):
        request = MockRequest()
        request.META['CONTENT_TYPE'] = 'application/xml'
        request.set_body('<objects></objects>')

        basic = BasicResource()
        data = basic.deserialize(request, request.body)

        self.assertEqual(data, [])

    def test_deserialize_no_contenttype_header(self):
        request = MockRequest()
        request.set_body('[]')

        basic = BasicResource()
        data = basic.deserialize(request, request.body)

        self.assertEqual(data, [])

    def test_fields(self):
        basic = BasicResource()
        self.assertEqual(len(basic.fields), 4)
        self.assert_('name' in basic.fields)
        self.assertEqual(isinstance(basic.fields['name'], fields.CharField), True)
        self.assertEqual(basic.fields['name']._resource, basic.__class__)
        self.assertEqual(basic.fields['name'].instance_name, 'name')
        self.assert_('view_count' in basic.fields)
        self.assertEqual(isinstance(basic.fields['view_count'], fields.IntegerField), True)
        self.assertEqual(basic.fields['view_count']._resource, basic.__class__)
        self.assertEqual(basic.fields['view_count'].instance_name, 'view_count')
        self.assert_('date_joined' in basic.fields)
        self.assertEqual(isinstance(basic.fields['date_joined'], fields.DateTimeField), True)
        self.assertEqual(basic.fields['date_joined']._resource, basic.__class__)
        self.assertEqual(basic.fields['date_joined'].instance_name, 'date_joined')
        self.assert_('resource_uri' in basic.fields)
        self.assertEqual(isinstance(basic.fields['resource_uri'], fields.CharField), True)
        self.assertEqual(basic.fields['resource_uri']._resource, basic.__class__)
        self.assertEqual(basic.fields['resource_uri'].instance_name, 'resource_uri')
        self.assertEqual(basic._meta.resource_name, 'basic')

        another = AnotherBasicResource()
        self.assertEqual(len(another.fields), 8)
        self.assert_('name' in another.fields)
        self.assertEqual(isinstance(another.name, fields.CharField), True)
        self.assertEqual(another.fields['name']._resource, another.__class__)
        self.assertEqual(another.fields['name'].instance_name, 'name')
        self.assert_('view_count' in another.fields)
        self.assertEqual(isinstance(another.view_count, fields.IntegerField), True)
        self.assertEqual(another.fields['view_count']._resource, another.__class__)
        self.assertEqual(another.fields['view_count'].instance_name, 'view_count')
        self.assert_('date_joined' in another.fields)
        self.assertEqual(isinstance(another.date_joined, fields.DateField), True)
        self.assertEqual(another.fields['date_joined']._resource, another.__class__)
        self.assertEqual(another.fields['date_joined'].instance_name, 'date_joined')
        self.assert_('is_active' in another.fields)
        self.assertEqual(isinstance(another.is_active, fields.BooleanField), True)
        self.assertEqual(another.fields['is_active']._resource, another.__class__)
        self.assertEqual(another.fields['is_active'].instance_name, 'is_active')
        self.assert_('aliases' in another.fields)
        self.assertEqual(isinstance(another.aliases, fields.ListField), True)
        self.assertEqual(another.fields['aliases']._resource, another.__class__)
        self.assertEqual(another.fields['aliases'].instance_name, 'aliases')
        self.assert_('meta' in another.fields)
        self.assertEqual(isinstance(another.meta, fields.DictField), True)
        self.assertEqual(another.fields['meta']._resource, another.__class__)
        self.assertEqual(another.fields['meta'].instance_name, 'meta')
        self.assert_('owed' in another.fields)
        self.assertEqual(isinstance(another.owed, fields.DecimalField), True)
        self.assertEqual(another.fields['owed']._resource, another.__class__)
        self.assertEqual(another.fields['owed'].instance_name, 'owed')
        self.assert_('resource_uri' in another.fields)
        self.assertEqual(isinstance(another.resource_uri, fields.CharField), True)
        self.assertEqual(another.fields['resource_uri']._resource, another.__class__)
        self.assertEqual(another.fields['resource_uri'].instance_name, 'resource_uri')
        self.assertEqual(another._meta.resource_name, 'anotherbasic')

        nouri = NoUriBasicResource()
        self.assertEqual(len(nouri.fields), 3)
        self.assert_('name' in nouri.fields)
        self.assertEqual(isinstance(nouri.name, fields.CharField), True)
        self.assertEqual(nouri.fields['name']._resource, nouri.__class__)
        self.assertEqual(nouri.fields['name'].instance_name, 'name')
        self.assert_('view_count' in nouri.fields)
        self.assertEqual(isinstance(nouri.view_count, fields.IntegerField), True)
        self.assertEqual(nouri.fields['view_count']._resource, nouri.__class__)
        self.assertEqual(nouri.fields['view_count'].instance_name, 'view_count')
        self.assert_('date_joined' in nouri.fields)
        self.assertEqual(isinstance(nouri.date_joined, fields.DateTimeField), True)
        self.assertEqual(nouri.fields['date_joined']._resource, nouri.__class__)
        self.assertEqual(nouri.fields['date_joined'].instance_name, 'date_joined')
        # Note - automatic resource naming.
        self.assertEqual(nouri._meta.resource_name, 'nouribasic')

    def test_inheritance(self):
        mrofr = MROFieldResource()
        self.assertEqual(len(mrofr.fields), 3)
        self.assertEqual(mrofr.fields['test'].default, 'test_a')
        self.assertEqual(mrofr.fields['name'].default, 'Mr. Field')

    def test_full_dehydrate_with_use_in(self):
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = aware_datetime(2010, 3, 30, 9, 0, 0)

        basic = BasicResourceWithDifferentListAndDetailFields()
        test_bundle_1 = basic.build_bundle(obj=test_object_1)

        # check hydration with details
        bundle_1 = basic.full_dehydrate(test_bundle_1)
        self.assertEqual(bundle_1.data['name'], 'Daniel')
        self.assertEqual(bundle_1.data['view_count'], 12)
        self.assertEqual(bundle_1.data.get('date_joined'), None)

        # now check dehydration with lists
        test_bundle_2 = basic.build_bundle(obj=test_object_1)

        bundle_2 = basic.full_dehydrate(test_bundle_2, for_list=True)
        self.assertEqual(bundle_2.data['name'], 'Daniel')
        self.assertEqual(bundle_2.data.get('view_count'), None)
        self.assertEqual(bundle_2.data['date_joined'].year, 2010)
        self.assertEqual(bundle_2.data['date_joined'].day, 30)

    def test_full_dehydrate_with_use_in_callable(self):
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = aware_datetime(2010, 3, 30, 9, 0, 0)

        basic = BasicResourceWithDifferentListAndDetailFieldsCallable()
        test_bundle_1 = basic.build_bundle(obj=test_object_1)

        # check hydration with details
        bundle_1 = basic.full_dehydrate(test_bundle_1)
        self.assertEqual(bundle_1.data['name'], 'Daniel')
        self.assertEqual(bundle_1.data['view_count'], 12)
        self.assertEqual(bundle_1.data.get('date_joined'), None)

        # now check dehydration with lists. Should be the same as details since
        # we are using callables for the use_in
        test_bundle_2 = basic.build_bundle(obj=test_object_1)

        bundle_2 = basic.full_dehydrate(test_bundle_2, for_list=True)
        self.assertEqual(bundle_2.data['name'], 'Daniel')
        self.assertEqual(bundle_2.data['view_count'], 12)
        self.assertEqual(bundle_2.data.get('date_joined'), None)

    def test_full_dehydrate(self):
        test_object_1 = TestObject()
        test_object_1.name = 'Daniel'
        test_object_1.view_count = 12
        test_object_1.date_joined = aware_datetime(2010, 3, 30, 9, 0, 0)
        test_object_1.foo = "Hi, I'm ignored."

        basic = BasicResource()
        test_bundle_1 = basic.build_bundle(obj=test_object_1)

        bundle_1 = basic.full_dehydrate(test_bundle_1)
        self.assertEqual(bundle_1.data['name'], 'Daniel')
        self.assertEqual(bundle_1.data['view_count'], 12)
        self.assertEqual(bundle_1.data['date_joined'].year, 2010)
        self.assertEqual(bundle_1.data['date_joined'].day, 30)
        self.assertEqual(bundle_1.data.get('bar'), None)

        # Now check the fallback behaviors.
        test_object_2 = TestObject()
        test_object_2.name = 'Daniel'
        basic_2 = BasicResource()
        test_bundle_2 = basic_2.build_bundle(obj=test_object_2)

        bundle_2 = basic_2.full_dehydrate(test_bundle_2)
        self.assertEqual(bundle_2.data['name'], 'Daniel')
        self.assertEqual(bundle_2.data['view_count'], 0)
        self.assertEqual(bundle_2.data['date_joined'].year, 2010)
        self.assertEqual(bundle_2.data['date_joined'].day, 27)

        test_object_3 = TestObject()
        test_object_3.name = 'Joe'
        test_object_3.view_count = 5
        test_object_3.created = aware_datetime(2010, 3, 29, 11, 0, 0)
        test_object_3.is_active = False
        test_object_3.bar = "But sometimes I'm not ignored!"
        another_1 = AnotherBasicResource()
        test_bundle_3 = another_1.build_bundle(obj=test_object_3)

        another_bundle_1 = another_1.full_dehydrate(test_bundle_3)
        self.assertEqual(another_bundle_1.data['name'], 'Joe')
        self.assertEqual(another_bundle_1.data['view_count'], 5)
        self.assertEqual(another_bundle_1.data['date_joined'].year, 2010)
        self.assertEqual(another_bundle_1.data['date_joined'].day, 29)
        self.assertEqual(another_bundle_1.data['is_active'], False)
        self.assertEqual(another_bundle_1.data['aliases'], ['Mr. Smith', 'John Doe'])
        self.assertEqual(another_bundle_1.data['meta'], {'threat': 'high'})
        self.assertEqual(another_bundle_1.data['owed'], Decimal('102.57'))
        self.assertEqual(another_bundle_1.data['bar'], "But sometimes I'm not ignored!")

    def test_full_hydrate(self):
        basic = BasicResource()
        basic_bundle_1 = Bundle(data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0)
        })

        # Now load up the data.
        hydrated = basic.full_hydrate(basic_bundle_1)

        self.assertEqual(hydrated.data['name'], 'Daniel')
        self.assertEqual(hydrated.data['view_count'], 6)
        self.assertEqual(hydrated.data['date_joined'], aware_datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hydrated.obj.name, 'Daniel')
        self.assertEqual(hydrated.obj.view_count, 6)
        self.assertEqual(hydrated.obj.date_joined, aware_datetime(2010, 2, 15, 12, 0, 0))

        another = AnotherBasicResource()
        another_bundle_1 = Bundle(data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0),
            'aliases': ['test', 'test1'],
            'meta': {'foo': 'bar'},
            'owed': '12.53',
        })

        # Now load up the data (without the ``bar`` key).
        hydrated = another.full_hydrate(another_bundle_1)

        self.assertEqual(hydrated.data['name'], 'Daniel')
        self.assertEqual(hydrated.data['view_count'], 6)
        self.assertEqual(hydrated.data['date_joined'], aware_datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hydrated.data['aliases'], ['test', 'test1'])
        self.assertEqual(hydrated.data['meta'], {'foo': 'bar'})
        self.assertEqual(hydrated.data['owed'], '12.53')
        self.assertEqual(hydrated.obj.name, 'Daniel')
        self.assertEqual(hydrated.obj.view_count, 6)
        self.assertEqual(hydrated.obj.date_joined, aware_datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hasattr(hydrated.obj, 'bar'), False)

        another_bundle_2 = Bundle(data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0),
            'bar': True,
        })

        # Now load up the data (this time with the ``bar`` key).
        hydrated = another.full_hydrate(another_bundle_2)

        self.assertEqual(hydrated.data['name'], 'Daniel')
        self.assertEqual(hydrated.data['view_count'], 6)
        self.assertEqual(hydrated.data['date_joined'], aware_datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hydrated.obj.name, 'Daniel')
        self.assertEqual(hydrated.obj.view_count, 6)
        self.assertEqual(hydrated.obj.date_joined, aware_datetime(2010, 2, 15, 12, 0, 0))
        self.assertEqual(hydrated.obj.bar, 'O HAI BAR!')

        # Test that a nullable value with a previous non-null value
        # can be set to None.
        nullable = NullableNameResource()
        obj = nullable._meta.object_class()
        obj.name = "Daniel"
        null_bundle = Bundle(obj=obj, data={'name': None})
        hydrated = nullable.full_hydrate(null_bundle)

        self.assertTrue(hydrated.obj.name is None)

        # Test that a nullable value with a previous non-null value
        # is not overridden if no value was given
        obj = nullable._meta.object_class()
        obj.name = "Daniel"
        empty_null_bundle = Bundle(obj=obj, data={})
        hydrated = nullable.full_hydrate(empty_null_bundle)

        self.assertEquals(hydrated.obj.name, "Daniel")

    def test_full_hydrate__can_put_null_to_clear_related_value(self):
        class RelatedBasicResource(BasicResource):
            parent = fields.ToOneField(BasicResource, 'parent', null=True, blank=True)
        basic = RelatedBasicResource()
        basic_bundle_1 = Bundle(data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': None,
            'parent': None
        })
        basic_bundle_1.obj = Mock()
        basic_bundle_1.obj.date_joined = aware_datetime(2010, 2, 15, 12, 0, 0)
        basic_bundle_1.obj.parent = Mock()

        self.assertEqual(basic_bundle_1.data['date_joined'], None)
        self.assertEqual(basic_bundle_1.data['parent'], None)
        self.assertNotEqual(basic_bundle_1.obj.date_joined, None)
        self.assertNotEqual(basic_bundle_1.obj.parent, None)

        # Now load up the data.
        hydrated = basic.full_hydrate(basic_bundle_1)

        self.assertEqual(hydrated.data['name'], 'Daniel')
        self.assertEqual(hydrated.data['view_count'], 6)
        self.assertEqual(hydrated.data['date_joined'], None)
        self.assertEqual(hydrated.data['parent'], None)
        self.assertEqual(hydrated.obj.name, 'Daniel')
        self.assertEqual(hydrated.obj.view_count, 6)
        self.assertEqual(hydrated.obj.date_joined, None)
        self.assertEqual(hydrated.obj.parent, None)

    def test_full_hydrate__does_not_overwrite_related_value_if_not_put(self):
        class RelatedBasicResource(BasicResource):
            parent = fields.ToOneField(BasicResource, 'parent', null=True, blank=True)
        basic = RelatedBasicResource()
        basic_bundle_1 = Bundle(data={
            'name': 'Daniel',
            'date_joined': None,
        })
        basic_bundle_1.obj = Mock()
        basic_bundle_1.obj.date_joined = aware_datetime(2010, 2, 15, 12, 0, 0)
        basic_bundle_1.obj.view_count = 3
        basic_bundle_1.obj.parent = Mock()

        self.assertNotEqual(basic_bundle_1.obj.view_count, None)
        self.assertNotEqual(basic_bundle_1.obj.parent, None)

        # Now load up the data.
        hydrated = basic.full_hydrate(basic_bundle_1)

        self.assertNotEqual(hydrated.obj.view_count, None)
        self.assertNotEqual(hydrated.obj.parent, None)

    def test_obj_get_list(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_get_list, bundle)

    def test_obj_delete_list(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_delete_list, bundle)

    def test_obj_get(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_get, bundle, pk=1)

    def test_obj_create(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_create, bundle)

    def test_obj_update(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_update, bundle)

    def test_obj_delete(self):
        basic = BasicResource()
        bundle = Bundle()
        self.assertRaises(NotImplementedError, basic.obj_delete, bundle)

    def test_rollback(self):
        basic = BasicResource()
        bundles_seen = []
        self.assertRaises(NotImplementedError, basic.rollback, bundles_seen)

    def test_build_schema(self):
        basic = BasicResource()
        schema = adjust_schema(basic.build_schema())
        expected_schema = {
            'allowed_detail_http_methods': ['get', 'post', 'put', 'delete', 'patch'],
            'allowed_list_http_methods': ['get', 'post', 'put', 'delete', 'patch'],
            'default_format': 'application/json',
            'default_limit': 20,
            'fields': {
                'date_joined': {
                    'blank': False,
                    'default': 'No default provided.',
                    'help_text': 'A date & time as a string. Ex: "2010-11-10T03:07:43"',
                    'nullable': True,
                    'verbose_name': "date joined",
                    'readonly': False,
                    'type': 'datetime',
                    'unique': False,
                    'primary_key': False,
                },
                'name': {
                    'blank': False,
                    'default': 'No default provided.',
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'nullable': False,
                    'verbose_name': "Basic name",
                    'readonly': False,
                    'type': 'string',
                    'unique': False,
                    'primary_key': False,
                },
                'resource_uri': {
                    'blank': False,
                    'default': 'No default provided.',
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'nullable': False,
                    'verbose_name': "resource uri",
                    'readonly': True,
                    'type': 'string',
                    'unique': False,
                    'primary_key': False,
                },
                'view_count': {
                    'blank': False,
                    'default': 0,
                    'help_text': 'Integer data. Ex: 2673',
                    'nullable': False,
                    'verbose_name': 'view count',
                    'readonly': False,
                    'type': 'integer',
                    'unique': False,
                    'primary_key': False,
                }
            }
        }
        self.assertEqual(schema, expected_schema)

    def test_build_schema__altered_meta(self):
        basic = BasicResource()
        basic._meta.ordering = ['date_joined', 'name']
        basic._meta.filtering = {'date_joined': ['gt', 'gte'], 'name': ALL}
        schema = adjust_schema(basic.build_schema())
        expected_schema = {
            'filtering': {
                'name': 1,
                'date_joined': ['gt', 'gte']
            },
            'allowed_detail_http_methods': ['get', 'post', 'put', 'delete', 'patch'],
            'ordering': ['date_joined', 'name'],
            'fields': {
                'view_count': {
                    'nullable': False,
                    'default': 0,
                    'help_text': 'Integer data. Ex: 2673',
                    'verbose_name': "view count",
                    'readonly': False,
                    'blank': False,
                    'help_text': 'Integer data. Ex: 2673',
                    'unique': False,
                    'type': 'integer',
                    "primary_key": False
                },
                'date_joined': {
                    'nullable': True,
                    'default': 'No default provided.',
                    'help_text': 'A date & time as a string. Ex: "2010-11-10T03:07:43"',
                    'verbose_name': "date joined",
                    'readonly': False,
                    'blank': False,
                    'help_text': 'A date & time as a string. Ex: "2010-11-10T03:07:43"',
                    'unique': False,
                    'type': 'datetime',
                    "primary_key": False
                },
                'name': {
                    'nullable': False,
                    'default': 'No default provided.',
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': "Basic name",
                    'readonly': False,
                    'blank': False,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                },
                'resource_uri': {
                    'nullable': False,
                    'default': 'No default provided.',
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': "resource uri",
                    'readonly': True,
                    'blank': False,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                }
            },
            'default_format': 'application/json',
            'default_limit': 20,
            'allowed_list_http_methods': ['get', 'post', 'put', 'delete', 'patch']
        }
        self.assertEqual(schema, expected_schema)

    def test_subclassing(self):
        class CommonMeta:
            default_format = 'application/xml'

        class MiniResource(Resource):
            abcd = fields.CharField(default='abcd')
            efgh = fields.IntegerField(default=1234)

            class Meta:
                resource_name = 'mini'

        mini = MiniResource()
        self.assertEqual(len(mini.fields), 3)

        class AnotherMiniResource(MiniResource):
            ijkl = fields.BooleanField(default=True)

            class Meta(CommonMeta):
                resource_name = 'anothermini'

        another = AnotherMiniResource()
        self.assertEqual(len(another.fields), 4)
        self.assertEqual(another._meta.default_format, 'application/xml')

    def test_method_check(self):
        basic = BasicResource()
        request = HttpRequest()
        request.method = 'GET'
        request.GET = {'format': 'json'}

        # No allowed methods. Kaboom.
        self.assertRaises(ImmediateHttpResponse, basic.method_check, request)

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            basic.method_check(request)
        e = ctx.exception
        self.assertEqual(e.response['Allow'], '')

        # Not an allowed request.
        self.assertRaises(ImmediateHttpResponse, basic.method_check, request, allowed=['post'])

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            basic.method_check(request, allowed=['post'])
        e = ctx.exception
        self.assertEqual(e.response['Allow'], 'POST')

        # Allowed (single).
        request_method = basic.method_check(request, allowed=['get'])
        self.assertEqual(request_method, 'get')

        # Allowed (unicode, for Python 2.* with `from __future__ import unicode_literals`)
        request_method = basic.method_check(request, allowed=[u'get'])

        # Allowed (multiple).
        request_method = basic.method_check(request, allowed=['post', 'get', 'put'])
        self.assertEqual(request_method, 'get')

        request = HttpRequest()
        request.method = 'POST'
        request.POST = {'format': 'json'}

        # Not an allowed request.
        self.assertRaises(ImmediateHttpResponse, basic.method_check, request, allowed=['get'])

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            basic.method_check(request, allowed=['get', 'put', 'delete', 'patch'])
        e = ctx.exception
        self.assertEqual(e.response['Allow'], 'GET,PUT,DELETE,PATCH')

        # Allowed (multiple).
        request_method = basic.method_check(request, allowed=['post', 'get', 'put'])
        self.assertEqual(request_method, 'post')

    def test_auth_check(self):
        basic = BasicResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}

        # Allowed (single).
        try:
            basic.is_authenticated(request)
        except ImmediateHttpResponse:
            self.fail()

    def test_create_response(self):
        basic = BasicResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}

        data = {'hello': 'world'}
        output = basic.create_response(request, data)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(force_str(output.content), '{"hello": "world"}')

        request.GET = {'format': 'xml'}
        data = {'objects': [{'hello': 'world', 'abc': 123}], 'meta': {'page': 1}}
        output = basic.create_response(request, data)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(force_str(output.content), '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<response><meta type="hash"><page type="integer">1</page></meta><objects type="list"><object type="hash"><abc type="integer">123</abc><hello>world</hello></object></objects></response>')

    def test_mangled(self):
        mangled = MangledBasicResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.user = 'mr_authed'

        data = Bundle(data={'hello': 'world'})
        output = mangled.alter_deserialized_detail_data(request, data)
        self.assertEqual(output.data, {'hello': 'world', 'user': 'mr_authed'})

        request.GET = {'format': 'xml'}
        data = {'objects': [{'hello': 'world', 'abc': 123}], 'meta': {'page': 1}}
        output = mangled.alter_list_data_to_serialize(request, data)
        self.assertEqual(output, {'testobjects': [{'abc': 123, 'hello': 'world'}]})

    def test_get_list_with_use_in(self):
        basic = BasicResourceWithDifferentListAndDetailFields()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        basic_resource_list = json.loads(force_str(basic.get_list(request).content))['objects']
        self.assertEquals(basic_resource_list[0]['name'], 'Daniel')
        self.assertEquals(basic_resource_list[0]['date_joined'], u'2010-03-30T09:00:00')

        self.assertNotIn('view_count', basic_resource_list[0])


# ====================
# Model-based tests...
# ====================

class DateRecordResource(ModelResource):
    class Meta:
        queryset = DateRecord.objects.all()
        always_return_data = True
        authorization = Authorization()

    def hydrate(self, bundle):
        bundle.data['message'] = bundle.data['message'].lower()
        return bundle

    def hydrate_username(self, bundle):
        bundle.data['username'] = bundle.data['username'].upper()
        return bundle


class NoteResource(ModelResource):
    class Meta:
        resource_name = 'notes'
        authorization = Authorization()
        filtering = {
            'content': ['startswith', 'exact'],
            'created': ALL,
            'title': ALL,
            'slug': ['exact'],
        }
        ordering = ['title', 'slug', 'resource_uri']
        queryset = Note.objects.filter(is_active=True)
        serializer = Serializer(formats=['json', 'jsonp', 'xml', 'yaml', 'plist'])

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/notes/'

        return '/api/v1/notes/%s/' % bundle_or_obj.obj.id


class NoQuerysetNoteResource(ModelResource):
    class Meta:
        resource_name = 'noqsnotes'
        authorization = Authorization()
        filtering = {
            'name': ALL,
        }
        object_class = Note


class LightlyCustomNoteResource(NoteResource):
    class Meta:
        resource_name = 'noteish'
        authorization = Authorization()
        allowed_methods = ['get']
        queryset = Note.objects.filter(is_active=True)


class TinyLimitNoteResource(NoteResource):
    class Meta:
        limit = 3
        resource_name = 'littlenote'
        authorization = Authorization()
        allowed_methods = ['get']
        queryset = Note.objects.filter(is_active=True)


class AlwaysDataNoteResource(NoteResource):
    class Meta:
        resource_name = 'alwaysdatanote'
        queryset = Note.objects.filter(is_active=True)
        always_return_data = True
        authorization = Authorization()


class AlwaysDataNoteResourceUseIn(NoteResource):
    author = fields.CharField(attribute='author__username', use_in="detail")
    constant = fields.IntegerField(default=20, use_in="list")

    class Meta:
        resource_name = 'alwaysdatanote'
        queryset = Note.objects.filter(is_active=True)
        always_return_data = True
        authorization = Authorization()


class NoteResourceNonUniqueDetailUriName(NoteResource):
    author = fields.CharField(attribute='author__username', use_in="detail")
    constant = fields.IntegerField(default=20, use_in="list")

    class Meta:
        resource_name = 'nonuniqueidnote'
        queryset = Note.objects.filter(is_active=True)
        always_return_data = True
        authorization = Authorization()
        detail_uri_name = 'slug'


class MyDefaultPKModelResource(ModelResource):
    class Meta:
        resource_name = 'mydefaultpkmodel'
        queryset = MyDefaultPKModel.objects.all()
        always_return_data = True
        authorization = Authorization()


if MyUUIDModel:
    class MyUUIDModelResourceNonUniqueDetailUriName(ModelResource):
        class Meta:
            resource_name = 'nonuniqueidmyuuidmodel'
            queryset = MyUUIDModel.objects.all()
            always_return_data = True
            authorization = Authorization()
            detail_uri_name = 'anotheruuid'

        def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
            if bundle_or_obj is None:
                return '/api/v1/nonuniqueidmyuuidmodel/'

            if hasattr(bundle_or_obj, 'obj'):
                bundle_or_obj = bundle_or_obj.obj
            return '/api/v1/nonuniqueidmyuuidmodel/%s/' % bundle_or_obj.anotheruuid

    class MyRelatedUUIDModelResource(ModelResource):
        myuuidmodels = fields.ManyToManyField(MyUUIDModelResourceNonUniqueDetailUriName, 'myuuidmodels', full=True)

        class Meta:
            resource_name = 'myrelateduuidmodel'
            queryset = MyRelatedUUIDModel.objects.all()
            always_return_data = True
            authorization = Authorization()


class VeryCustomNoteResource(NoteResource):
    author = fields.CharField(attribute='author__username')
    constant = fields.IntegerField(default=20)

    class Meta:
        authorization = Authorization()
        limit = 50
        resource_name = 'notey'
        serializer = CustomSerializer()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put']
        queryset = Note.objects.all()
        fields = ['title', 'content', 'created', 'is_active']


class AutoNowNoteResource(ModelResource):
    class Meta:
        resource_name = 'autonownotes'
        queryset = AutoNowNote.objects.filter(is_active=True)
        authorization = Authorization()

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/autonownotes/'

        return '/api/v1/autonownotes/%s/' % bundle_or_obj.obj.id


class BigAutoNowModelResource(ModelResource):
    class Meta:
        resource_name = 'bigautonowmodels'
        queryset = BigAutoNowModel.objects.all()
        authorization = Authorization()

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/bigautonowmodels/'

        return '/api/v1/bigautonowmodels/%s/' % bundle_or_obj.obj.id


class CustomPaginator(Paginator):
    def page(self):
        data = super(CustomPaginator, self).page()
        data['extra'] = 'Some extra stuff here.'
        return data


class CustomPageNoteResource(NoteResource):
    class Meta:
        limit = 10
        resource_name = 'pagey'
        paginator_class = CustomPaginator
        queryset = Note.objects.all()
        authorization = Authorization()


class AlwaysUserNoteResource(NoteResource):
    class Meta:
        resource_name = 'noteish'
        queryset = Note.objects.filter(is_active=True)
        authorization = Authorization()

    def get_object_list(self, request):
        return super(AlwaysUserNoteResource, self).get_object_list(request).filter(author=request.user)


class UseInNoteResource(NoteResource):

    content = fields.CharField(attribute='content', use_in='detail')
    title = fields.CharField(attribute='title', use_in='list')

    class Meta:
        queryset = Note.objects.all()
        authorization = Authorization()


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        authorization = Authorization()
        filtering = {
            'id': ALL,
            'username': ALL,
        }

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/users/'

        return '/api/v1/users/%s/' % bundle_or_obj.obj.id


class DetailedNoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'author')
    hello_world = fields.CharField(default='world')

    class Meta:
        resource_name = 'detailednotes'
        filtering = {
            'content': ['startswith', 'exact'],
            'title': ALL,
            'slug': ['exact'],
            'user': ALL,
            'hello_world': ['exact'],  # Note this is invalid for filtering.
        }
        ordering = ['title', 'slug', 'user']
        queryset = Note.objects.filter(is_active=True)
        authorization = Authorization()

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/notes/'

        return '/api/v1/notes/%s/' % bundle_or_obj.obj.id


class DetailedNoteResourceWithHydrate(DetailedNoteResource):
    def hydrate(self, bundle):
        bundle.data['user'] = bundle.request.user  # This should fail using TastyPie 0.9.11 if triggered in patch_list
        return bundle


class RequiredFKNoteResource(ModelResource):
    editor = fields.ForeignKey(UserResource, 'editor')

    class Meta:
        resource_name = 'requiredfknotes'
        queryset = NoteWithEditor.objects.all()
        authorization = Authorization()


class NoAttributeFKNoteResource(ModelResource):
    editor = fields.ForeignKey(UserResource, None)

    class Meta:
        resource_name = 'noattrfknotes'
        queryset = NoteWithEditor.objects.all()
        authorization = Authorization()


class FunctionAttributeFKNoteResource(ModelResource):
    editor = fields.ForeignKey(UserResource, lambda bundle: User.objects.first(), null=True)

    class Meta:
        resource_name = 'fnattrfknotes'
        queryset = NoteWithEditor.objects.all()
        authorization = Authorization()


class ThrottledNoteResource(NoteResource):
    class Meta:
        resource_name = 'throttlednotes'
        queryset = Note.objects.filter(is_active=True)
        throttle = CacheThrottle(throttle_at=2, timeframe=5, expiration=5)
        authorization = Authorization()


class BasicAuthNoteResource(NoteResource):
    class Meta:
        resource_name = 'notes'
        queryset = Note.objects.filter(is_active=True)
        authentication = BasicAuthentication()
        authorization = Authorization()


class NoUriNoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
        include_resource_uri = False
        authorization = Authorization()


class WithAbsoluteURLNoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
        include_absolute_url = True
        resource_name = 'withabsoluteurlnote'
        authorization = Authorization()

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is None:
            return '/api/v1/withabsoluteurlnote/'

        return '/api/v1/withabsoluteurlnote/%s/' % bundle_or_obj.obj.id


class AlternativeCollectionNameNoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.filter(is_active=True)
        collection_name = 'alt_objects'
        authorization = Authorization()


class SubjectResource(ModelResource):
    class Meta:
        queryset = Subject.objects.all()
        resource_name = 'subjects'
        filtering = {
            'name': ALL,
        }
        authorization = Authorization()


class RelatedNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', verbose_name='The Author')
    subjects = fields.ManyToManyField(SubjectResource, 'subjects')

    class Meta:
        queryset = Note.objects.all()
        resource_name = 'relatednotes'
        filtering = {
            'author': ALL,
            'subjects': ALL_WITH_RELATIONS,
        }
        fields = ['title', 'slug', 'content', 'created', 'is_active']
        authorization = Authorization()


class AnotherSubjectResource(ModelResource):
    notes = fields.ToManyField(DetailedNoteResource, 'notes')

    class Meta:
        queryset = Subject.objects.all()
        resource_name = 'anothersubjects'
        excludes = ['notes']
        filtering = {
            'notes': ALL_WITH_RELATIONS,
        }
        authorization = Authorization()


class AnotherRelatedNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author')
    subjects = fields.ManyToManyField(SubjectResource, 'subjects', full=True)

    class Meta:
        queryset = Note.objects.all()
        resource_name = 'relatednotes'
        filtering = {
            'author': ALL,
            'subjects': ALL_WITH_RELATIONS,
        }
        fields = ['title', 'slug', 'content', 'created', 'is_active']
        authorization = Authorization()


class YetAnotherRelatedNoteResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)
    subjects = fields.ManyToManyField(SubjectResource, 'subjects')

    class Meta:
        queryset = Note.objects.all()
        resource_name = 'relatednotes'
        filtering = {
            'author': ALL,
            'subjects': ALL_WITH_RELATIONS,
        }
        fields = ['title', 'slug', 'content', 'created', 'is_active']
        authorization = Authorization()


class NullableRelatedNoteResource(AnotherRelatedNoteResource):
    author = fields.ForeignKey(UserResource, 'author', null=True)
    subjects = fields.ManyToManyField(SubjectResource, 'subjects', null=True)


class NullableBlankRelatedNoteResource(AnotherRelatedNoteResource):
    author = fields.ForeignKey(UserResource, 'author', null=True, blank=True)
    subjects = fields.ManyToManyField(SubjectResource, 'subjects', null=True)


class NullableMediaBitResource(ModelResource):
    # The old (broke) way to allow ``note`` to be omitted, even though it's a required field.
    note = fields.ToOneField(NoteResource, 'note', null=True)

    class Meta:
        queryset = MediaBit.objects.all()
        resource_name = 'nullablemediabit'
        authorization = Authorization()


class ReadOnlyRelatedNoteResource(ModelResource):
    author = fields.ToOneField(UserResource, 'author', readonly=True)
    my_property = fields.CharField(attribute='my_property', null=True, readonly=True)

    class Meta:
        queryset = Note.objects.all()
        authorization = Authorization()


class BlankMediaBitResource(ModelResource):
    # Allow ``note`` to be omitted, even though it's a required field.
    note = fields.ToOneField(NoteResource, 'note', blank=True)

    class Meta:
        queryset = MediaBit.objects.all()
        resource_name = 'blankmediabit'
        authorization = Authorization()

    # We'll custom populate the note here if it's not present.
    # Doesn't make a ton of sense in this context, but for things
    # like ``user`` or ``site`` that you can autopopulate based
    # on the request.
    def hydrate_note(self, bundle):
        if not bundle.data.get('note'):
            bundle.obj.note = Note.objects.get(pk=1)

        return bundle


class TestOptionsResource(ModelResource):
    class Meta:
        queryset = Note.objects.all()
        allowed_methods = ['post']
        list_allowed_methods = ['post', 'put']
        authorization = Authorization()


# Per user authorization bits.
class PerUserAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        if bundle.request and hasattr(bundle.request, 'user'):
            if bundle.request.user.is_authenticated:
                object_list = object_list.filter(author=bundle.request.user)
            else:
                object_list = object_list.none()

        return object_list


class PerUserNoteResource(NoteResource):
    class Meta:
        resource_name = 'perusernotes'
        queryset = Note.objects.all()
        authorization = PerUserAuthorization()

    def authorized_read_list(self, object_list, bundle):
        if object_list._result_cache is not None:
            self._pre_limits = len(object_list._result_cache)
        else:
            self._pre_limits = 0

        # Just to demonstrate the per-resource hooks.
        new_object_list = super(PerUserNoteResource, self).authorized_read_list(object_list, bundle)

        if object_list._result_cache is not None:
            self._post_limits = len(object_list._result_cache)
        else:
            self._post_limits = 0

        return new_object_list.filter(is_active=True)
# End per user authorization bits.


# Per object authorization bits.
class PerObjectAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # Does a per-object check that "can't" be expressed as part of a
        # ``QuerySet``. This helps test that all objects in the ``QuerySet``
        # aren't loaded & evaluated, only results that match the request.
        final_list = []

        for obj in object_list:
            # Only match ``Note`` objects with 'post' in the title.
            if 'post' in obj.title.lower():
                final_list.append(obj)

        return final_list


class PerObjectNoteResource(NoteResource):
    class Meta:
        resource_name = 'perobjectnotes'
        queryset = Note.objects.all()
        authorization = PerObjectAuthorization()
        filtering = {
            'is_active': ALL,
        }

    def authorized_read_list(self, object_list, bundle):
        if object_list._result_cache is not None:
            self._pre_limits = len(object_list._result_cache)
        else:
            self._pre_limits = 0

        # Check the QuerySet cache to make sure we haven't populated everything.
        new_object_list = super(PerObjectNoteResource, self).authorized_read_list(object_list, bundle)

        self._post_limits = len(object_list._result_cache)
        return new_object_list
# End per object authorization bits.


class CounterResource(ModelResource):
    count = fields.IntegerField('count', default=0, null=True)

    class Meta:
        queryset = Counter.objects.all()
        authorization = Authorization()

    def full_hydrate(self, bundle):
        bundle.times_hydrated = getattr(bundle, 'times_hydrated', 0) + 1
        new_shiny = super(CounterResource, self).full_hydrate(bundle)
        new_shiny.obj.count = new_shiny.times_hydrated
        return new_shiny


class CounterAuthorization(Authorization):
    def create_detail(self, object_list, bundle, *args, **kwargs):
        bundle._create_auth_call_count = getattr(bundle, '_create_auth_call_count', 0) + 1
        return True

    def update_detail(self, object_list, bundle, *args, **kwargs):
        bundle._update_auth_call_count = getattr(bundle, '_update_auth_call_count', 0) + 1
        return True


class CounterCreateDetailResource(ModelResource):
    count = fields.IntegerField('count', default=0, null=True)

    class Meta:
        queryset = Counter.objects.all()
        authorization = CounterAuthorization()


class CounterUpdateDetailResource(ModelResource):
    count = fields.IntegerField('count', default=0, null=True)

    class Meta:
        queryset = Counter.objects.all()
        authorization = CounterAuthorization()


@override_settings(ROOT_URLCONF='core.tests.resource_urls')
class ModelResourceTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def setUp(self):
        self.maxDiff = None
        super(ModelResourceTestCase, self).setUp()
        self.note_1 = Note.objects.get(pk=1)
        self.subject_1 = Subject.objects.create(
            name='News',
            url='/news/'
        )
        self.subject_2 = Subject.objects.create(
            name='Photos',
            url='/photos/'
        )
        self.note_1.subjects.add(self.subject_1)
        self.note_1.subjects.add(self.subject_2)

    def tearDown(self):
        cache.clear()

    @patch('django.core.signals.got_request_exception.send')
    @patch('tastypie.resources.ModelResource.obj_get_list', side_effect=IOError)
    def test_exception_handling(self, obj_get_list_mock, send_signal_mock):
        request = HttpRequest()
        request.method = 'GET'
        resource = NoteResource()
        resource.wrap_view('dispatch_list')(request)
        self.assertTrue(obj_get_list_mock.called, msg="Test invalid: obj_get_list should have been dispatched")
        self.assertTrue(send_signal_mock.called, msg="got_request_exception was not called after an error")

    def test_escaping(self):
        request = HttpRequest()
        request.method = 'GET'
        request.GET = {
            'limit': '<script>alert(1)</script>',
        }
        resource = NoteResource()
        res = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(res.status_code, 400)
        err_data = json.loads(res.content.decode('utf-8'))
        self.assertTrue('&lt;script&gt;alert(1)&lt;/script&gt;' in err_data['error'])

    def test_init(self):
        # Very minimal & stock.
        resource_1 = NoteResource()
        self.assertEqual(len(resource_1.fields), 8)
        self.assertNotEqual(resource_1._meta.queryset, None)
        self.assertEqual(resource_1._meta.resource_name, 'notes')
        self.assertEqual(resource_1._meta.limit, 20)
        self.assertEqual(resource_1._meta.list_allowed_methods, ['get', 'post', 'put', 'delete', 'patch'])
        self.assertEqual(resource_1._meta.detail_allowed_methods, ['get', 'post', 'put', 'delete', 'patch'])
        self.assertEqual(isinstance(resource_1._meta.serializer, Serializer), True)

        # Lightly custom.
        resource_2 = LightlyCustomNoteResource()
        self.assertEqual(len(resource_2.fields), 8)
        self.assertNotEqual(resource_2._meta.queryset, None)
        self.assertEqual(resource_2._meta.resource_name, 'noteish')
        self.assertEqual(resource_2._meta.limit, 20)
        self.assertEqual(resource_2._meta.list_allowed_methods, ['get'])
        self.assertEqual(resource_2._meta.detail_allowed_methods, ['get'])
        self.assertEqual(isinstance(resource_2._meta.serializer, Serializer), True)

        # Highly custom.
        resource_3 = VeryCustomNoteResource()
        self.assertEqual(len(resource_3.fields), 7)
        self.assertNotEqual(resource_3._meta.queryset, None)
        self.assertEqual(resource_3._meta.resource_name, 'notey')
        self.assertEqual(resource_3._meta.limit, 50)
        self.assertEqual(resource_3._meta.list_allowed_methods, ['get'])
        self.assertEqual(resource_3._meta.detail_allowed_methods, ['get', 'post', 'put'])
        self.assertEqual(isinstance(resource_3._meta.serializer, CustomSerializer), True)

        # Note - automatic resource naming.
        resource_4 = NoUriNoteResource()
        self.assertEqual(resource_4._meta.resource_name, 'nourinote')

        # Test to make sure that, even with a mix of basic & advanced
        # configuration, options are set right.
        resource_5 = TestOptionsResource()
        self.assertEqual(resource_5._meta.allowed_methods, ['post'])
        # Should be the overridden values.
        self.assertEqual(resource_5._meta.list_allowed_methods, ['post', 'put'])
        # Should inherit from the basic configuration.
        self.assertEqual(resource_5._meta.detail_allowed_methods, ['post'])

        resource_6 = CustomPageNoteResource()
        self.assertEqual(resource_6._meta.paginator_class, CustomPaginator)

        # FK fields with non-string attributes
        resource_7 = NoAttributeFKNoteResource()
        self.assertEqual(len(resource_7.fields), 9)
        resource_8 = FunctionAttributeFKNoteResource()
        self.assertEqual(len(resource_8.fields), 9)

    def test_can_create(self):
        resource_1 = NoteResource()
        self.assertEqual(resource_1.can_create(), True)

        resource_2 = LightlyCustomNoteResource()
        self.assertEqual(resource_2.can_create(), False)

    def test_can_update(self):
        resource_1 = NoteResource()
        self.assertEqual(resource_1.can_update(), True)

        resource_2 = LightlyCustomNoteResource()
        self.assertEqual(resource_2.can_update(), False)

        resource_3 = TestOptionsResource()
        self.assertEqual(resource_3.can_update(), True)

    def test_can_delete(self):
        resource_1 = NoteResource()
        self.assertEqual(resource_1.can_delete(), True)

        resource_2 = LightlyCustomNoteResource()
        self.assertEqual(resource_2.can_delete(), False)

    def test_fields(self):
        # Different from the ``ResourceTestCase.test_fields``, we're checking
        # some related bits here & self-referential bits later on.
        resource_1 = RelatedNoteResource()
        self.assertEqual(len(resource_1.fields), 8)
        self.assert_('author' in resource_1.fields)
        self.assertTrue(isinstance(resource_1.fields['author'], fields.ToOneField))
        self.assertEqual(resource_1.fields['author']._resource, resource_1.__class__)
        self.assertEqual(resource_1.fields['author'].instance_name, 'author')
        self.assertTrue('subjects' in resource_1.fields)
        self.assertTrue(isinstance(resource_1.fields['subjects'], fields.ToManyField))
        self.assertEqual(resource_1.fields['subjects']._resource, resource_1.__class__)
        self.assertEqual(resource_1.fields['subjects'].instance_name, 'subjects')

        # Sanity check the other introspected fields.
        annr = AutoNowNoteResource()
        self.assertEqual(len(annr.fields), 8)
        self.assertEqual(sorted(annr.fields.keys()), ['content', 'created', 'id', 'is_active', 'resource_uri', 'slug', 'title', 'updated'])

        self.assertTrue(isinstance(annr.fields['content'], fields.CharField))
        self.assertEqual(annr.fields['content'].attribute, 'content')
        self.assertEqual(annr.fields['content'].blank, True)
        self.assertEqual(annr.fields['content']._default, '')
        self.assertEqual(annr.fields['content'].instance_name, 'content')
        self.assertEqual(annr.fields['content'].null, False)
        self.assertEqual(annr.fields['content'].readonly, False)
        self.assertEqual(annr.fields['content'].unique, False)

        self.assertTrue(isinstance(annr.fields['created'], fields.DateTimeField))
        self.assertEqual(annr.fields['created'].attribute, 'created')
        self.assertEqual(annr.fields['created'].blank, False)
        self.assertTrue(isinstance(annr.fields['created']._default(), datetime.datetime))
        self.assertEqual(annr.fields['created'].instance_name, 'created')
        self.assertEqual(annr.fields['created'].null, True)
        self.assertEqual(annr.fields['created'].readonly, False)
        self.assertEqual(annr.fields['created'].unique, False)

        self.assertTrue(isinstance(annr.fields['id'], fields.IntegerField))
        self.assertEqual(annr.fields['id'].attribute, 'id')
        self.assertEqual(annr.fields['id'].blank, True)
        self.assertEqual(annr.fields['id']._default, '')
        self.assertEqual(annr.fields['id'].instance_name, 'id')
        self.assertEqual(annr.fields['id'].null, False)
        self.assertEqual(annr.fields['id'].readonly, False)
        self.assertEqual(annr.fields['id'].unique, True)

        self.assertTrue(isinstance(annr.fields['is_active'], fields.BooleanField))
        self.assertEqual(annr.fields['is_active'].attribute, 'is_active')
        self.assertEqual(annr.fields['is_active'].blank, True)
        self.assertEqual(annr.fields['is_active']._default, True)
        self.assertEqual(annr.fields['is_active'].instance_name, 'is_active')
        self.assertEqual(annr.fields['is_active'].null, False)
        self.assertEqual(annr.fields['is_active'].readonly, False)
        self.assertEqual(annr.fields['is_active'].unique, False)

        self.assertTrue(isinstance(annr.fields['resource_uri'], fields.CharField))
        self.assertEqual(annr.fields['resource_uri'].attribute, None)
        self.assertEqual(annr.fields['resource_uri'].blank, False)
        self.assertEqual(annr.fields['resource_uri']._default, fields.NOT_PROVIDED)
        self.assertEqual(annr.fields['resource_uri'].instance_name, 'resource_uri')
        self.assertEqual(annr.fields['resource_uri'].null, False)
        self.assertEqual(annr.fields['resource_uri'].readonly, True)
        self.assertEqual(annr.fields['resource_uri'].unique, False)

        self.assertTrue(isinstance(annr.fields['slug'], fields.CharField))
        self.assertEqual(annr.fields['slug'].attribute, 'slug')
        self.assertEqual(annr.fields['slug'].blank, False)
        self.assertEqual(annr.fields['slug']._default, fields.NOT_PROVIDED)
        self.assertEqual(annr.fields['slug'].instance_name, 'slug')
        self.assertEqual(annr.fields['slug'].null, False)
        self.assertEqual(annr.fields['slug'].readonly, False)
        self.assertEqual(annr.fields['slug'].unique, True)

        self.assertTrue(isinstance(annr.fields['title'], fields.CharField))
        self.assertEqual(annr.fields['title'].attribute, 'title')
        self.assertEqual(annr.fields['title'].blank, False)
        self.assertEqual(annr.fields['title']._default, fields.NOT_PROVIDED)
        self.assertEqual(annr.fields['title'].instance_name, 'title')
        self.assertEqual(annr.fields['title'].null, False)
        self.assertEqual(annr.fields['title'].readonly, False)
        self.assertEqual(annr.fields['title'].unique, False)

        self.assertTrue(isinstance(annr.fields['updated'], fields.DateTimeField))
        self.assertEqual(annr.fields['updated'].attribute, 'updated')
        self.assertEqual(annr.fields['updated'].blank, True)
        self.assertTrue(isinstance(annr.fields['updated']._default(), datetime.datetime))
        self.assertEqual(annr.fields['updated'].instance_name, 'updated')
        self.assertEqual(annr.fields['updated'].null, False)
        self.assertEqual(annr.fields['updated'].readonly, False)
        self.assertEqual(annr.fields['updated'].unique, False)

    def test_big_auto_field(self):
        annr = BigAutoNowModelResource()
        self.assertEqual(len(annr.fields), 2)
        self.assertEqual(sorted(annr.fields.keys()), ['id', 'resource_uri'])

        self.assertTrue(isinstance(annr.fields['id'], fields.IntegerField))
        self.assertEqual(annr.fields['id'].attribute, 'id')
        self.assertEqual(annr.fields['id'].blank, True)
        self.assertEqual(annr.fields['id']._default, '')
        self.assertEqual(annr.fields['id'].instance_name, 'id')
        self.assertEqual(annr.fields['id'].null, False)
        self.assertEqual(annr.fields['id'].readonly, False)
        self.assertEqual(annr.fields['id'].unique, True)

    def test_invalid_model_resource(self):
        """
        Test error message regarding ModelResource lacking object_class and queryset.
        """
        with self.assertRaises(ImproperlyConfigured) as exception_context:
            class InvalidNoteResource(ModelResource):
                class Meta:
                    resource_name = 'invalidnotes'
        self.assertTrue('InvalidNoteResource' in str(exception_context.exception))

    def test_abstract_model_resource(self):
        """
        Abstract ModelResource classes don't require object_class or queryset,
        should skip populating fields and url details.
        """
        class AbstractNoteResource(ModelResource):
            class Meta:
                abstract = True

        # AbstractNoteResource should have none of the dynamic attributes generated on declaration
        for attr in ('object_class', 'queryset', 'fields', 'base_fields', 'absolute_url'):
            self.assertFalse(getattr(AbstractNoteResource, attr, False),
                             "AbstractNoteResource has non-falsey %s" % attr)

    def test_abstract_resource_subclass_good(self):
        """
        Subclassing an abstract base resource should work as expected.
        """
        class AbstractNoteResource(ModelResource):
            class Meta:
                abstract = True

        class ConcreteNoteResource(AbstractNoteResource):
            class Meta:
                queryset = Note.objects.all()
        resource = ConcreteNoteResource(api_name='v1')
        resource_fields = set(resource.fields.keys())
        self.assertEqual(resource_fields, {
            'updated',
            'title',
            'created',
            'is_active',
            'id',
            'content',
            'slug',
            'resource_uri',
        })

    def test_abstract_resource_subclass_bad(self):
        """
        Subclassing an abstract base resource requires model_class or queryset.
        """
        class AbstractNoteResource(ModelResource):
            class Meta:
                abstract = True

        with self.assertRaises(ImproperlyConfigured):
            class ConcreteNoteResource(AbstractNoteResource):
                class Meta:
                    fields = []

    def test_fields__empty_list(self):
        class EmptyFieldsNoteResource(ModelResource):
            class Meta:
                resource_name = 'emptyfieldsnotes'
                object_class = Note
                fields = []

        resource = EmptyFieldsNoteResource(api_name='v1')

        self.assertEqual(set(resource.fields.keys()), {'resource_uri'})

    def test_fields__empty_list_on_subclass(self):
        class FieldsNotSpecifiedNoteResource(ModelResource):
            class Meta:
                resource_name = 'nofieldsnotes'
                object_class = Note

        class EmptyFieldsNoteResource(FieldsNotSpecifiedNoteResource):
            class Meta(FieldsNotSpecifiedNoteResource.Meta):
                resource_name = 'emptyfieldsnotes'
                fields = []

        resource = EmptyFieldsNoteResource(api_name='v1')

        self.assertEqual(set(resource.fields.keys()), {'resource_uri'})

    def test_fields__list_omitted(self):
        class FieldsNotSpecifiedNoteResource(ModelResource):
            class Meta:
                resource_name = 'nofieldsnotes'
                object_class = Note

        resource = FieldsNotSpecifiedNoteResource(api_name='v1')

        self.assertEqual(set(resource.fields.keys()), {
            'updated',
            'title',
            'created',
            'is_active',
            'id',
            'content',
            'slug',
            'resource_uri',
        })

    def test_urls(self):
        # The common case, where the ``Api`` specifies the name.
        resource = NoteResource(api_name='v1')
        patterns = resource.urls
        self.assertEqual(len(patterns), 4)
        self.assertEqual([pattern.name for pattern in patterns], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'])
        self.assertEqual(reverse('api_dispatch_list', kwargs={
            'api_name': 'v1',
            'resource_name': 'notes',
        }), '/api/v1/notes/')
        self.assertEqual(reverse('api_dispatch_detail', kwargs={
            'api_name': 'v1',
            'resource_name': 'notes',
            'pk': 1,
        }), '/api/v1/notes/1/')

        # Start over.
        resource = NoteResource()
        patterns = resource.urls
        self.assertEqual(len(patterns), 4)
        self.assertEqual([pattern.name for pattern in patterns], ['api_dispatch_list', 'api_get_schema', 'api_get_multiple', 'api_dispatch_detail'])
        self.assertEqual(reverse('api_dispatch_list', urlconf='core.tests.manual_urls', kwargs={
            'resource_name': 'notes',
        }), '/notes/')
        self.assertEqual(reverse('api_dispatch_detail', urlconf='core.tests.manual_urls', kwargs={
            'resource_name': 'notes',
            'pk': 1,
        }), '/notes/1/')

    def test__get_via_uri(self):
        resource = NoteResource(api_name='v1')
        note_1 = resource.get_via_uri('/api/v1/notes/1/')
        self.assertEqual(note_1.pk, 1)

    def test__get_via_uri__app_name_same_as_resource(self):
        resource = NoteResource(api_name='v1')
        # Should work even if app name is the same as resource
        note_1 = resource.get_via_uri('/notes/api/v1/notes/1/')
        self.assertEqual(note_1.pk, 1)

    def test__get_via_uri__identifier_contains_resource_name(self):
        class CustomNoteResource(NoteResource):
            class Meta(NoteResource.Meta):
                detail_uri_name = 'slug'
        resource = CustomNoteResource(api_name='v1')
        note_1 = Note.objects.first()
        note_1.slug = 'notes1-notes'
        note_1.save()
        note_1_new = resource.get_via_uri('/notes/api/v1/notes/%s/' % note_1.slug)
        self.assertEqual(note_1_new.pk, note_1.pk)

    def test__get_via_uri__identifier_same_as_resource_name(self):
        class CustomNoteResource(NoteResource):
            class Meta(NoteResource.Meta):
                detail_uri_name = 'slug'
        resource = CustomNoteResource(api_name='v1')
        note_1 = Note.objects.first()
        note_1.slug = 'notes'
        note_1.save()
        note_1_new = resource.get_via_uri('/notes/api/v1/notes/%s/' % note_1.slug)
        self.assertEqual(note_1_new.pk, note_1.pk)

    def test__get_via_uri__uri_has_special_chars(self):
        resource = NoteResource(api_name='v1')
        note_1 = resource.get_via_uri('/~krichy/api/v1/notes/1/')
        self.assertEqual(note_1.pk, 1)

    def test__get_via_uri__uri_has_encoded_special_chars(self):
        resource = NoteResource(api_name='v1')
        note_1 = resource.get_via_uri('/%7ekrichy/api/v1/notes/1/')
        self.assertEqual(note_1.pk, 1)

    def test__get_via_uri__invalid_uri(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('http://example.com/')

    def test__get_via_uri__bad_uri_containing_resource_name(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('/notes/api/v1/photos/1/')

    def test__get_via_uri__bad_resource_name_contains_resource_name(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('/notes/api/v1/foonotes/1/')

    def test__get_via_uri__nonexistant_resource(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('/api/v1/foo/1/')

    def test__get_via_uri__different_resource(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('/api/v1/photos/1/')

    def test__get_via_uri__list_uri(self):
        resource = NoteResource(api_name='v1')
        with self.assertRaises(NotFound):
            resource.get_via_uri('/api/v1/notes/')

    def test__get_via_uri__with_request(self):
        resource = NoteResource(api_name='v1')
        # Check with the request.
        request = HttpRequest()
        note_1 = resource.get_via_uri('/api/v1/notes/1/', request=request)
        self.assertEqual(note_1.pk, 1)

    def test_create_identifier(self):
        resource = NoteResource()
        new_note = Note.objects.get(pk=1)
        self.assertEqual(resource.create_identifier(new_note), 'core.note.1')

    def test_determine_format(self):
        resource = NoteResource()
        request = HttpRequest()

        # Default.
        self.assertEqual(resource.determine_format(request), 'application/json')

        # Test forcing the ``format`` parameter.
        request.GET = {'format': 'json'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        request.GET = {'format': 'jsonp'}
        self.assertEqual(resource.determine_format(request), 'text/javascript')

        request.GET = {'format': 'xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')

        request.GET = {'format': 'yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')

        request.GET = {'format': 'foo'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        # Test the ``Accept`` header.
        request.META = {'HTTP_ACCEPT': 'application/json'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        request.META = {'HTTP_ACCEPT': 'text/javascript'}
        self.assertEqual(resource.determine_format(request), 'text/javascript')

        request.META = {'HTTP_ACCEPT': 'application/xml'}
        self.assertEqual(resource.determine_format(request), 'application/xml')

        request.META = {'HTTP_ACCEPT': 'text/yaml'}
        self.assertEqual(resource.determine_format(request), 'text/yaml')

        # unsupported text/html should return default format
        request.META = {'HTTP_ACCEPT': 'text/html'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        # unsupported applicaiton/octet-stream returns default format
        request.META = {'HTTP_ACCEPT': 'application/octet-stream'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        request.META = {'HTTP_ACCEPT': 'application/json,application/xml;q=0.9,*/*;q=0.8'}
        self.assertEqual(resource.determine_format(request), 'application/json')

        request.META = {'HTTP_ACCEPT': 'text/plain,application/xml,application/json;q=0.9,*/*;q=0.8'}
        self.assertEqual(resource.determine_format(request), 'application/xml')

        # your typical browser (chrome, firefoxs, no plugins) should get back xml
        request.META = {'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        self.assertEqual(resource.determine_format(request), 'application/xml')

    def test_build_schema(self):
        self.maxDiff = None
        related = RelatedNoteResource(api_name='v1')
        schema = adjust_schema(related.build_schema())
        expected_schema = {
            'filtering': {
                'subjects': 2,
                'author': 1
            },
            'allowed_detail_http_methods': ['get', 'post', 'put', 'delete', 'patch'],
            'fields': {
                'author': {
                    'related_type': 'to_one',
                    'related_schema': '/api/v1/user/schema/',
                    'nullable': False,
                    'default': 'No default provided.',
                    'readonly': False,
                    'blank': False,
                    'help_text': 'A single related resource. Can be either a URI or set of nested resource data.',
                    'verbose_name': 'The Author',
                    'unique': False,
                    'type': 'related',
                    "primary_key": False
                },
                'title': {
                    'nullable': False,
                    'default': 'No default provided.',
                    'readonly': False,
                    'blank': False,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': 'The Title',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                },
                'created': {
                    'nullable': False,
                    'default': 'The current date.',
                    'readonly': False,
                    'blank': False,
                    'help_text': 'A date & time as a string. Ex: "2010-11-10T03:07:43"',
                    'verbose_name': 'created',
                    'unique': False,
                    'type': 'datetime',
                    "primary_key": False
                },
                'is_active': {
                    'nullable': False,
                    'default': True,
                    'readonly': False,
                    'blank': True,
                    'help_text': 'Boolean data. Ex: True',
                    'verbose_name': 'is active',
                    'unique': False,
                    'type': 'boolean',
                    "primary_key": False
                },
                'content': {
                    'nullable': False,
                    'default': '',
                    'readonly': False,
                    'blank': True,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': 'content',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                },
                'subjects': {
                    'related_type': 'to_many',
                    'related_schema': '/api/v1/subjects/schema/',
                    'nullable': False,
                    'default': 'No default provided.',
                    'readonly': False,
                    'blank': False,
                    'help_text': 'Many related resources. Can be either a list of URIs or list of individually nested resource data.',
                    'verbose_name': 'subjects',
                    'unique': False,
                    'type': 'related',
                    "primary_key": False
                },
                'slug': {
                    'nullable': False,
                    'default': 'No default provided.',
                    'readonly': False,
                    'blank': False,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': 'slug',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                },
                'resource_uri': {
                    'nullable': False,
                    'default': 'No default provided.',
                    'readonly': True,
                    'blank': False,
                    'help_text': 'Unicode string data. Ex: "Hello World"',
                    'verbose_name': 'resource uri',
                    'unique': False,
                    'type': 'string',
                    "primary_key": False
                }
            },
            'default_format': 'application/json',
            'default_limit': 20,
            'allowed_list_http_methods': ['get', 'post', 'put', 'delete', 'patch']
        }
        self.assertEqual(schema, expected_schema)

    def test_build_filters(self):
        resource = NoteResource()

        # Valid none.
        self.assertEqual(resource.build_filters(), {})
        self.assertEqual(resource.build_filters(filters=None), {})

        # Not in the filtering dict.
        self.assertEqual(resource.build_filters(filters={'resource_url__exact': '/foo/bar/'}), {})

        # Filter valid but disallowed.
        self.assertRaises(InvalidFilterError, resource.build_filters, filters={'slug__startswith': 'whee'})

        # Skipped due to not being recognized.
        self.assertEqual(resource.build_filters(filters={'moof__exact': 'baz'}), {})

        # Invalid simple (implicit ``__exact``).
        self.assertEqual(resource.build_filters(filters={'title': 'Hello world.'}), {'title__exact': 'Hello world.'})

        # Valid simple (explicit ``__exact``).
        self.assertEqual(resource.build_filters(filters={'title__exact': 'Hello world.'}), {'title__exact': 'Hello world.'})

        # Valid in (using ``,``).
        self.assertEqual(resource.build_filters(filters={'title__in': ''}), {'title__in': ''})
        self.assertEqual(resource.build_filters(filters={'title__in': 'foo'}), {'title__in': ['foo']})
        self.assertEqual(resource.build_filters(filters={'title__in': 'foo,bar'}), {'title__in': ['foo', 'bar']})

        # Valid in (using multiple params).
        self.assertEqual(resource.build_filters(filters=QueryDict('title__in=foo&title__in=bar')), {'title__in': ['foo', 'bar']})
        self.assertEqual(resource.build_filters(filters=QueryDict('title__in=foo,bar')), {'title__in': ['foo', 'bar']})

        # Valid simple (non-``__exact``).
        self.assertEqual(resource.build_filters(filters={'content__startswith': 'Hello'}), {'content__startswith': 'Hello'})

        # Valid boolean.
        self.assertEqual(resource.build_filters(filters={'title': 'true'}), {'title__exact': True})
        self.assertEqual(resource.build_filters(filters={'title': 'True'}), {'title__exact': True})
        self.assertEqual(resource.build_filters(filters={'title': True}), {'title__exact': True})
        self.assertEqual(resource.build_filters(filters={'title': 'false'}), {'title__exact': False})
        self.assertEqual(resource.build_filters(filters={'title': 'False'}), {'title__exact': False})
        self.assertEqual(resource.build_filters(filters={'title': False}), {'title__exact': False})
        self.assertEqual(resource.build_filters(filters={'title': 'nil'}), {'title__exact': None})
        self.assertEqual(resource.build_filters(filters={'title': 'none'}), {'title__exact': None})
        self.assertEqual(resource.build_filters(filters={'title': 'None'}), {'title__exact': None})
        self.assertEqual(resource.build_filters(filters={'title': None}), {'title__exact': None})

        # Valid multiple.
        self.assertEqual(resource.build_filters(filters={
            'slug__exact': 'Hello',
            'title__exact': 'RAGE',
            'content__startswith': 'A thing here.'
        }), {'slug__exact': 'Hello', 'content__startswith': 'A thing here.', 'title__exact': 'RAGE'})

        # Valid multiple (model attribute differs from field name).
        resource_2 = DetailedNoteResource()
        filters_1 = {
            'slug__exact': 'Hello',
            'title__exact': 'RAGE',
            'content__startswith': 'A thing here.',
            'user__gt': 2,
        }
        self.assertEqual(resource_2.build_filters(filters=filters_1), {'title__exact': 'RAGE', 'slug__exact': 'Hello', 'author__gt': 2, 'content__startswith': 'A thing here.'})

        # No relationship traversal to the filter, please.
        resource_3 = RelatedNoteResource()
        self.assertRaises(InvalidFilterError, resource_3.build_filters, filters={'author__username__startswith': 'j'})

        # Allow relationship traversal.
        self.assertEqual(resource_3.build_filters(filters={'subjects__name__startswith': 'News'}), {'subjects__name__startswith': 'News'})

        # Ensure related fields that do not have filtering throw an exception.
        self.assertRaises(InvalidFilterError, resource_3.build_filters, filters={'subjects__url__startswith': 'News'})

        # Ensure related fields that do not exist throw an exception.
        self.assertRaises(InvalidFilterError, resource_3.build_filters, filters={'subjects__foo__startswith': 'News'})

        # Check where the field name doesn't match the database relation.
        resource_4 = AnotherSubjectResource()
        self.assertEqual(resource_4.build_filters(filters={'notes__user__startswith': 'Daniel'}), {'notes__author__startswith': 'Daniel'})

        # Make sure build_filters works even on resources without queryset
        resource = NoQuerysetNoteResource()
        self.assertEqual(resource.build_filters(), {})

    def test_build_filters_bad(self):
        """
        Test that a nonsensical filter fails validation.
        """
        resource = AnotherSubjectResource()
        # Make sure that fields that don't have attributes can't be filtered on.
        self.assertRaises(InvalidFilterError, resource.build_filters, filters={'notes__hello_world': 'News'})

    def test_custom_build_filters(self):
        """
        A test derived from an example in the documentation (under Advanced Filtering).
        Mostly exists to exercise build_filters - if this test fails due to underlying
        framework changes, both this test and docs/resources.rst will need to be updated.
        """
        class MyResource(NoteResource):
            def build_filters(self, filters=None, **kwargs):
                if filters is None:
                    filters = {}

                orm_filters = super(MyResource, self).build_filters(filters, **kwargs)
                if 'title' in filters:
                    orm_filters['pk__in'] = Note.objects.filter(title=filters['title']).values_list('pk', flat=True)

                return orm_filters

        resource = MyResource()
        first_note = Note.objects.first()
        note = resource.obj_get(resource.build_bundle(), title=first_note.title)
        self.assertEqual(note, first_note)

    def test_xss_regressions(self):
        # Make sure the body is JSON & the content-type is right.
        resource = RelatedNoteResource()
        request = HttpRequest()
        request.method = 'GET'

        request.GET = {
            'format': 'xml',
            'author__username__startswith': 'j',
        }
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp['content-type'], 'application/xml; charset=utf-8')
        self.assertEqual(resp.content.decode('utf-8'), "<?xml version='1.0' encoding='utf-8'?>\n<response><error>Lookups are not allowed more than one level deep on the 'author' field.</error></response>")

        request.GET = {
            'format': 'json',
            'author__<script>alert("XSS")</script>': 'j',
        }
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.content.decode('utf-8'), '{"error": "Lookups are not allowed more than one level deep on the \'author\' field."}')

        request.GET = {
            'format': 'json',
            'limit': '<img%20src="http://ycombinator.com/images/y18.gif">',
        }
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.content.decode('utf-8'), '{"error": "Invalid limit \'&lt;img%20src=\\"http://ycombinator.com/images/y18.gif\\"&gt;\' provided. Please provide a positive integer."}')

        request.GET = {
            'format': 'json',
            'limit': '<img%20src="http://ycombinator.com/images/y18.gif">',
        }
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.content.decode('utf-8'), '{"error": "Invalid limit \'&lt;img%20src=\\"http://ycombinator.com/images/y18.gif\\"&gt;\' provided. Please provide a positive integer."}')

        request.GET = {
            'format': 'json',
            'offset': '<script>alert("XSS")</script>',
        }
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.content.decode('utf-8'), '{"error": "Invalid offset \'&lt;script&gt;alert(\\"XSS\\")&lt;/script&gt;\' provided. Please provide an integer."}')

    def test_apply_sorting(self):
        resource = NoteResource()
        base_bundle = Bundle()

        # Valid none.
        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list)
        self.assertEqual([obj.id for obj in ordered_list], [1, 2, 4, 6])

        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options=None)
        self.assertEqual([obj.id for obj in ordered_list], [1, 2, 4, 6])

        # Not a valid field.
        object_list = resource.obj_get_list(base_bundle)
        self.assertRaises(InvalidSortError, resource.apply_sorting, object_list, options={'order_by': 'foobar'})

        # Not in the ordering dict.
        object_list = resource.obj_get_list(base_bundle)
        self.assertRaises(InvalidSortError, resource.apply_sorting, object_list, options={'order_by': 'content'})

        # No attribute to sort by.
        object_list = resource.obj_get_list(base_bundle)
        self.assertRaises(InvalidSortError, resource.apply_sorting, object_list, options={'order_by': 'resource_uri'})

        # Valid ascending.
        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'order_by': 'title'})
        self.assertEqual([obj.id for obj in ordered_list], [2, 1, 6, 4])

        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'order_by': 'slug'})
        self.assertEqual([obj.id for obj in ordered_list], [2, 1, 6, 4])

        # Valid descending.
        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'order_by': '-title'})
        self.assertEqual([obj.id for obj in ordered_list], [4, 6, 1, 2])

        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'order_by': '-slug'})
        self.assertEqual([obj.id for obj in ordered_list], [4, 6, 1, 2])

        # Ensure the deprecated parameter still works.
        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'sort_by': '-title'})
        self.assertEqual([obj.id for obj in ordered_list], [4, 6, 1, 2])

        # Valid combination.
        object_list = resource.obj_get_list(base_bundle)
        ordered_list = resource.apply_sorting(object_list, options={'order_by': ['title', '-slug']})
        self.assertEqual([obj.id for obj in ordered_list], [2, 1, 6, 4])

        # Valid (model attribute differs from field name).
        resource_2 = DetailedNoteResource(base_bundle)
        object_list = resource_2.obj_get_list(base_bundle)
        ordered_list = resource_2.apply_sorting(object_list, options={'order_by': '-user'})
        self.assertEqual([obj.id for obj in ordered_list], [6, 4, 2, 1])

        # Invalid relation.
        resource_2 = DetailedNoteResource()
        object_list = resource_2.obj_get_list(base_bundle)
        ordered_list = resource_2.apply_sorting(object_list, options={'order_by': '-user__baz'})

        with self.assertRaises(FieldError):
            [obj.id for obj in ordered_list]

        # Valid relation.
        resource_2 = DetailedNoteResource()
        object_list = resource_2.obj_get_list(base_bundle)
        ordered_list = resource_2.apply_sorting(object_list, options={'order_by': 'user__id'})
        self.assertEqual([obj.id for obj in ordered_list], [1, 2, 4, 6])

        resource_2 = DetailedNoteResource()
        object_list = resource_2.obj_get_list(base_bundle)
        ordered_list = resource_2.apply_sorting(object_list, options={'order_by': '-user__id'})
        self.assertEqual([obj.id for obj in ordered_list], [6, 4, 2, 1])

        # Valid relational combination.
        resource_2 = DetailedNoteResource()
        object_list = resource_2.obj_get_list(base_bundle)
        ordered_list = resource_2.apply_sorting(object_list, options={'order_by': ['-user__username', 'title']})
        self.assertEqual([obj.id for obj in ordered_list], [2, 1, 6, 4])

    def test_get_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}

        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]}')

        # Test slicing.
        # First an invalid offset.
        request.GET = {'format': 'json', 'offset': 'abc', 'limit': 1}
        with self.assertRaises(BadRequest):
            resp = resource.get_list(request)

        # Try again with ``wrap_view`` for sanity.
        resp = resource.wrap_view('get_list')(request)
        self.assertEqual(resp.status_code, 400)

        # Then an out of range offset.
        request.GET = {'format': 'json', 'offset': -1, 'limit': 1}
        with self.assertRaises(BadRequest):
            resp = resource.get_list(request)

        # Then an out of range limit.
        request.GET = {'format': 'json', 'offset': 0, 'limit': -1}
        with self.assertRaises(BadRequest):
            resp = resource.get_list(request)

        # Valid slice.
        request.GET = {'format': 'json', 'offset': 0, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 2)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertTrue('/api/v1/notes/?' in list_data['meta']['next'])
        self.assertTrue('format=json' in list_data['meta']['next'])
        self.assertTrue('limit=2' in list_data['meta']['next'])
        self.assertTrue('offset=2' in list_data['meta']['next'])
        self.assertEqual(list_data['objects'], [
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            }
        ])

        # Valid, slightly overlapping slice.
        request.GET = {'format': 'json', 'offset': 1, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 2)
        self.assertEqual(list_data['meta']['offset'], 1)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertTrue('/api/v1/notes/?' in list_data['meta']['next'])
        self.assertTrue('format=json' in list_data['meta']['next'])
        self.assertTrue('limit=2' in list_data['meta']['next'])
        self.assertTrue('offset=3' in list_data['meta']['next'])
        self.assertEqual(list_data['objects'], [
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            }
        ])

        # Valid, non-overlapping slice.
        request.GET = {'format': 'json', 'offset': 3, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 2)
        self.assertEqual(list_data['meta']['offset'], 3)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertTrue('/api/v1/notes/?' in list_data['meta']['previous'])
        self.assertTrue('format=json' in list_data['meta']['previous'])
        self.assertTrue('limit=2' in list_data['meta']['previous'])
        self.assertTrue('offset=1' in list_data['meta']['previous'])
        self.assertEqual(list_data['objects'], [
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            }
        ])

        # Valid, but beyond the bounds slice.
        request.GET = {'format': 'json', 'offset': 100, 'limit': 2}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 2)
        self.assertEqual(list_data['meta']['offset'], 100)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertTrue('/api/v1/notes/?' in list_data['meta']['previous'])
        self.assertTrue('format=json' in list_data['meta']['previous'])
        self.assertTrue('limit=2' in list_data['meta']['previous'])
        self.assertTrue('offset=98' in list_data['meta']['previous'])
        self.assertEqual(list_data['objects'], [])

        # Valid slice, fetch all results.
        request.GET = {'format': 'json', 'offset': 0, 'limit': 0}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 1000)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertEqual(list_data['objects'], [
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            },
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            }
        ])

        # Valid sorting.
        request.GET = {'format': 'json', 'order_by': 'title'}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 20)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertEqual(list_data['objects'], [
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            }
        ])

        request.GET = {'format': 'json', 'order_by': '-title'}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 20)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertEqual(list_data['objects'], [
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            },
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            },
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            }
        ])

        # invalid sorting
        request.GET = {'format': 'json', 'order_by': 'monkey'}
        resp = resource.wrap_view('get_list')(request)
        self.assertEqual(resp.status_code, 400)
        res = json.loads(resp.content.decode('utf-8'))
        self.assertTrue('error' in res.keys())
        self.assertTrue('monkey' in res['error'])  # Error looks like "No matching \'monkey\' field for ordering on.

        # Test to make sure we're not inadvertently caching the QuerySet.
        request.GET = {'format': 'json'}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 20)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 4)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertEqual(list_data['objects'], [
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            },
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            }
        ])
        new_note = Note.objects.create(
            title='Another fresh note.',
            slug='another-fresh-note',
            content='Whee!',
            created=aware_datetime(2010, 7, 21, 11, 23),
            updated=aware_datetime(2010, 7, 21, 11, 23),
        )
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 20)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 5)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertEqual(list_data['meta']['next'], None)
        self.assertEqual(list_data['objects'], [
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            },
            {
                "content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!",
                "created": "2010-04-02T10:05:00",
                "id": 6,
                "is_active": True,
                "resource_uri": "/api/v1/notes/6/",
                "slug": "grannys-gone",
                "title": "Granny\'s Gone",
                "updated": "2010-04-02T10:05:00"
            },
            {
                "content": "Whee!",
                "created": "2010-07-21T11:23:00",
                "id": 7,
                "is_active": True,
                "resource_uri": "/api/v1/notes/7/",
                "slug": "another-fresh-note",
                "title": "Another fresh note.",
                "updated": make_naive(new_note.updated).isoformat()
            }
        ])

        # Regression - Ensure that the limit on the Resource gets used if
        # no other limit is requested.
        resource = TinyLimitNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}

        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        list_data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(list_data['meta']['limit'], 3)
        self.assertEqual(list_data['meta']['offset'], 0)
        self.assertEqual(list_data['meta']['total_count'], 5)
        self.assertEqual(list_data['meta']['previous'], None)
        self.assertTrue('/api/v1/notes/?' in list_data['meta']['next'])
        self.assertTrue('format=json' in list_data['meta']['next'])
        self.assertTrue('limit=3' in list_data['meta']['next'])
        self.assertTrue('offset=3' in list_data['meta']['next'])
        self.assertEqual(list_data['objects'], [
            {
                "content": "This is my very first post using my shiny new API. Pretty sweet, huh?",
                "created": "2010-03-30T20:05:00",
                "id": 1,
                "is_active": True,
                "resource_uri": "/api/v1/notes/1/",
                "slug": "first-post",
                "title": "First Post!",
                "updated": "2010-03-30T20:05:00"
            },
            {
                "content": "The dog ate my cat today. He looks seriously uncomfortable.",
                "created": "2010-03-31T20:05:00",
                "id": 2,
                "is_active": True,
                "resource_uri": "/api/v1/notes/2/",
                "slug": "another-post",
                "title": "Another Post",
                "updated": "2010-03-31T20:05:00"
            },
            {
                "content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.",
                "created": "2010-04-01T20:05:00",
                "id": 4,
                "is_active": True,
                "resource_uri": "/api/v1/notes/4/",
                "slug": "recent-volcanic-activity",
                "title": "Recent Volcanic Activity.",
                "updated": "2010-04-01T20:05:00"
            }
        ])

    def test_get_list_use_in(self):
        resource = UseInNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        resp = resource.get_list(request)
        self.assertEqual(resp.status_code, 200)
        resp = json.loads(resp.content.decode('utf-8'))
        for note in resp['objects']:
            self.assertNotIn('content', note)

    def test_get_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}

        resp = resource.get_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')

        resp = resource.get_detail(request, pk=2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}')

        resp = resource.get_detail(request, pk=300)
        self.assertEqual(resp.status_code, 404)

    def test_get_detail_use_in(self):
        resource = UseInNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        resp = resource.get_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        resp = json.loads(resp.content.decode('utf-8'))
        self.assertNotIn('title', resp)

    def test_put_list(self):
        resource = NoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'

        self.assertEqual(Note.objects.count(), 6)
        request.set_body('{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}]}')

        resp = resource.put_list(request)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        self.assertEqual(resp.content.decode('utf-8'), '')
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(Note.objects.filter(is_active=True).count(), 1)
        new_note = Note.objects.get(slug='cat-is-back-again')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")

        always_resource = AlwaysDataNoteResource()
        resp = always_resource.put_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.decode('utf-8').startswith('{"objects": ['))

    def test_put_list_with_use_in(self):
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'

        self.assertEqual(Note.objects.count(), 6)
        request.set_body('{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}]}')

        always_resource = AlwaysDataNoteResourceUseIn()
        resp = always_resource.put_list(request)
        self.assertEqual(resp.status_code, 200)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertTrue(len(content['objects']) == 1)
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

    def test_put_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "baddata": "some data"}')

        resp = resource.put_detail(request, pk=10)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")

        request.set_body('{"content": "The cat is gone again. I think it was the rabbits that ate him this time.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Gone", "updated": "2010-04-03 20:05:00"}')

        resp = resource.put_detail(request, pk=10)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, u'The cat is gone again. I think it was the rabbits that ate him this time.')

        always_resource = AlwaysDataNoteResource()
        resp = always_resource.put_detail(request, pk=10)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue("id" in data)
        self.assertEqual(data["id"], 10)
        self.assertTrue("content" in data)
        self.assertEqual(data["content"], "The cat is gone again. I think it was the rabbits that ate him this time.")
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)
        self.assertFalse("baddata" in data)

        # Now make sure we can null-out a relation.
        # Associate some data first.
        new_note = Note.objects.get(slug='cat-is-back')
        new_note.author = User.objects.get(username='johndoe')
        new_note.save()
        nullable_resource = NullableRelatedNoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00", "author": null}')

        resp = nullable_resource.put_detail(request, pk=10)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.author, None)

        # Test for issue 1489, if blank=True, PUT would clobber existing values if field not sent
        new_note = Note.objects.create(slug='cat-is-back-again')
        author = User.objects.create(username='johndoer')
        new_note.author = author
        new_note.save()
        nullable_resource = NullableBlankRelatedNoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2016-12-12 14:10:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2016-12-12 14:10:00"}')

        resp = nullable_resource.put_detail(request, pk=new_note.pk)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        new_note = Note.objects.get(slug='cat-is-back-again')
        self.assertEqual(new_note.author, author)

    def test_put_detail_with_always_return(self):
        # Check for issue #1576
        resource = AlwaysDataNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        resp = resource.get_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        resp = json.loads(resp.content.decode('utf-8'))

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body(json.dumps(resp))
        putresp = resource.put_detail(request, pk=1)
        self.assertEqual(putresp.status_code, 200)
        data = json.loads(putresp.content.decode('utf-8'))

        self.assertEqual(set(data.keys()), set(['title', 'slug', 'content', 'is_active', 'created', 'updated', 'id', 'resource_uri']))

    def test_put_detail_with_use_in(self):
        new_note = Note.objects.get(slug='another-post')
        new_note.author = User.objects.get(username='johndoe')
        new_note.save()

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}')

        always_resource = AlwaysDataNoteResourceUseIn()
        resp = always_resource.put_detail(request, pk=new_note.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue("id" in data)
        self.assertEqual(data["id"], new_note.pk)
        self.assertTrue("author" in data)
        self.assertFalse("constant" in data)
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)

    def test_put_detail_with_identifiers(self):
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"date": "2012-09-07", "username": "WAT", "message": "hello"}')

        date_record_resource = DateRecordResource()
        resp = date_record_resource.put_detail(request, username="maraujop")

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data['username'], "MARAUJOP")

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"date": "WAT", "username": "maraujop", "message": "hello"}')

        date_record_resource = DateRecordResource()
        resp = date_record_resource.put_detail(request, date="2012-09-07")

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data['date'], "2012-09-07")

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"date": "2012-09-07", "username": "maraujop", "message": "WAT"}')
        date_record_resource = DateRecordResource()
        resp = date_record_resource.put_detail(request, message="HELLO")

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(data['message'], "hello")

    def test_put_detail_with_non_unique_detail_uri_name(self):
        """
        Make sure when something besides 'pk' is used for detail_uri_name and
        it isn't unique that we still look up the correct object and don't
        create a duplicate.
        """
        self.assertFalse(Note._meta.get_field('slug').unique)

        new_note = Note.objects.get(slug='another-post')
        new_note.author = User.objects.get(username='johndoe')
        new_note.save()

        self.assertEqual(Note.objects.count(), 6)

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}')

        resource = NoteResourceNonUniqueDetailUriName()
        resp = resource.put_detail(request, slug=new_note.slug)

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(Note.objects.count(), 6)

        data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(data["id"], new_note.pk)
        self.assertEqual(data["slug"], new_note.slug)
        self.assertTrue("author" in data)
        self.assertFalse("constant" in data)
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)

    @skipIf(MyUUIDModel is None, 'UUIDField not available')
    def test_put_detail_with_non_unique_uuid_detail_uri_name(self):
        """
        Make sure when something besides 'pk' is used for detail_uri_name and
        it isn't unique that we still look up the correct object and don't
        create a duplicate.
        """
        self.assertFalse(MyUUIDModel._meta.get_field('anotheruuid').unique)

        myuuidmodel = MyUUIDModel.objects.create()

        self.assertEqual(MyUUIDModel.objects.count(), 1)

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back."}')

        resource = MyUUIDModelResourceNonUniqueDetailUriName()
        resp = resource.put_detail(request, anotheruuid=myuuidmodel.anotheruuid)

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(MyUUIDModel.objects.count(), 1)

        data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(data['id'], str(myuuidmodel.pk))
        self.assertEqual(data['anotheruuid'], str(myuuidmodel.anotheruuid))
        self.assertNotEqual(data['content'], '')

    @skipIf(MyUUIDModel is None, 'UUIDField not available')
    def test_patch_detail_with_m2m_non_unique_uuid_detail_uri_name(self):
        """
        Make sure when something besides 'pk' is used for detail_uri_name and
        it isn't unique that we still look up the correct object and don't
        create a duplicate.
        Make sure this still works when used as a related resource.
        """
        self.assertFalse(MyUUIDModel._meta.get_field('anotheruuid').unique)

        myuuidmodel = MyUUIDModel.objects.create()
        myrelateduuidmodel = MyRelatedUUIDModel.objects.create()
        myrelateduuidmodel.myuuidmodels.add(myuuidmodel)

        self.assertEqual(MyUUIDModel.objects.count(), 1)
        self.assertEqual(MyRelatedUUIDModel.objects.count(), 1)

        data = {
            'myuuidmodels': [
                {
                    'content': 'foo',
                    'resource_uri': MyUUIDModelResourceNonUniqueDetailUriName().get_resource_uri(myuuidmodel)
                },
                {
                    'content': 'bar',
                    'order': 1,
                }
            ]
        }

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body(json.dumps(data))

        self.assertNotEqual(myuuidmodel.content, data['myuuidmodels'][0]['content'])

        resource = MyRelatedUUIDModelResource()
        resp = resource.patch_detail(request, pk=myrelateduuidmodel.pk)

        self.assertEqual(resp.status_code, 202)

        self.assertEqual(MyUUIDModel.objects.count(), 2)
        self.assertEqual(MyRelatedUUIDModel.objects.count(), 1)

        myuuidmodel = MyUUIDModel.objects.get(pk=myuuidmodel.pk)

        self.assertEqual(myuuidmodel.content, data['myuuidmodels'][0]['content'])

        resp_data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(resp_data['myuuidmodels'][0]['id'], str(myuuidmodel.pk))
        self.assertEqual(resp_data['myuuidmodels'][0]['anotheruuid'], str(myuuidmodel.anotheruuid))
        self.assertEqual(resp_data['myuuidmodels'][0]['content'], data['myuuidmodels'][0]['content'])
        self.assertEqual(resp_data['myuuidmodels'][1]['content'], data['myuuidmodels'][1]['content'])

    def test_put_detail_with_default_pk(self):
        obj = MyDefaultPKModel.objects.create()

        self.assertEqual(MyDefaultPKModel.objects.count(), 1)

        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'PUT'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back."}')

        resource = MyDefaultPKModelResource()
        resp = resource.put_detail(request, pk=obj.pk)

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(MyDefaultPKModel.objects.count(), 1)

        data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(data["id"], obj.pk)
        self.assertNotEqual(data["content"], '')

    def test_post_list(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'
        request.set_body('{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}')

        resp = resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='cat-is-back')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")

        always_resource = AlwaysDataNoteResource()
        resp = always_resource.post_list(request)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue("id" in data)
        self.assertEqual(data["id"], 8)
        self.assertTrue("content" in data)
        self.assertEqual(data["content"], "The cat is back. The dog coughed him up out back.")
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)

    def test_post_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'POST'

        resp = resource.post_detail(request, pk=2)
        self.assertEqual(resp.status_code, 501)

    def test_delete_list(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'DELETE'

        resp = resource.delete_list(request)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        # Only the non-actives are left alive.
        self.assertEqual(Note.objects.count(), 2)

    def test_delete_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'DELETE'

        resp = resource.delete_detail(request, pk=2)
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Content-Type', resp)
        self.assertEqual(Note.objects.count(), 5)

    def test_patch_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False

        self.assertEqual(Note.objects.count(), 6)
        request._raw_post_data = request._body = '{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}, {"resource_uri": "/api/v1/notes/2/", "content": "This is note 2."}], "deleted_objects": ["/api/v1/notes/1/"]}'

        resp = resource.patch_list(request)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.content.decode('utf-8'), '')
        self.assertEqual(Note.objects.count(), 6)
        self.assertEqual(Note.objects.filter(is_active=True).count(), 4)
        new_note = Note.objects.get(slug='cat-is-back-again')
        self.assertEqual(new_note.content, "The cat is back. The dog coughed him up out back.")
        updated_note = Note.objects.get(pk=2)
        self.assertEqual(updated_note.content, "This is note 2.")

    def test_patch_list_return_data(self):
        always_resource = AlwaysDataNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False

        self.assertEqual(Note.objects.count(), 6)
        request._raw_post_data = request._body = '{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}, {"resource_uri": "/api/v1/alwaysdatanote/2/", "content": "This is note 2."}], "deleted_objects": ["/api/v1/alwaysdatanote/1/"]}'

        resp = always_resource.patch_list(request)
        self.assertEqual(resp.status_code, 202)
        self.assertTrue(resp.content.decode('utf-8').startswith('{"objects": ['))

    def test_patch_list_return_data_use_in(self):
        always_resource = AlwaysDataNoteResourceUseIn()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False

        self.assertEqual(Note.objects.count(), 6)
        request._raw_post_data = request._body = '{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-is-back-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}, {"resource_uri": "/api/v1/alwaysdatanote/2/", "content": "This is note 2."}], "deleted_objects": ["/api/v1/alwaysdatanote/1/"]}'

        resp = always_resource.patch_list(request)
        self.assertEqual(resp.status_code, 202)

        content = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(len(content['objects']), 2)
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

    def test_patch_list_bad_resource_uri(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False

        self.assertEqual(Note.objects.count(), 6)
        request._raw_post_data = request._body = '{"objects": [{"resource_uri": "/api/v1/notes/99999/", "content": "This is an invalid resource_uri", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "invalid-uri", "title": "Invalid URI", "updated": "2010-04-03 20:05:00"}]}'

        resp = resource.patch_list(request)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.content.decode('utf-8'), '')
        self.assertEqual(Note.objects.count(), 7)
        new_note = Note.objects.get(slug='invalid-uri')
        self.assertEqual(new_note.content, "This is an invalid resource_uri")

    def test_patch_list_with_request_data(self):
        """
        Verify that request data is accessible in a Resource's hydrate method after patch_list.
        """
        resource = DetailedNoteResourceWithHydrate()
        request = HttpRequest()
        request.user = User.objects.get(username='johndoe')
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False  # Not sure what this line does, copied from above
        request._raw_post_data = request._body = '{"objects": [{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00", "is_active": true, "slug": "cat-again-again", "title": "The Cat Is Back", "updated": "2010-04-03 20:05:00"}]}'

        resp = resource.patch_list(request)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.content.decode('utf-8'), '')
        self.assertEqual(Note.objects.filter(author=request.user, slug="cat-again-again").count(), 1)  # Validate that request.user was successfully passed in

    def test_patch_detail(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False
        request._raw_post_data = request._body = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00"}'

        resp = resource.patch_detail(request, pk=10)
        self.assertEqual(resp.status_code, 404)

        resp = resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Note.objects.count(), 6)
        note = Note.objects.get(pk=1)
        self.assertEqual(note.content, "The cat is back. The dog coughed him up out back.")
        self.assertEqual(note.created, aware_datetime(2010, 4, 3, 20, 5))

        request._raw_post_data = request._body = '{"content": "The cat is gone again. I think it was the rabbits that ate him this time."}'

        resp = resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Note.objects.count(), 6)
        new_note = Note.objects.get(pk=1)
        self.assertEqual(new_note.content, u'The cat is gone again. I think it was the rabbits that ate him this time.')

        always_resource = AlwaysDataNoteResource()
        request._raw_post_data = request._body = '{"content": "Wait, now the cat is back."}'
        resp = always_resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue("id" in data)
        self.assertEqual(data["id"], 1)
        self.assertTrue("content" in data)
        self.assertEqual(data["content"], u'Wait, now the cat is back.')
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)

    def test_patch_detail_use_in(self):
        self.assertEqual(Note.objects.count(), 6)
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'PATCH'
        request._read_started = False
        request._raw_post_data = request._body = '{"content": "The cat is back. The dog coughed him up out back.", "created": "2010-04-03 20:05:00"}'

        resp = resource.patch_detail(request, pk=10)
        self.assertEqual(resp.status_code, 404)

        resp = resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Note.objects.count(), 6)
        note = Note.objects.get(pk=1)
        self.assertEqual(note.content, "The cat is back. The dog coughed him up out back.")
        self.assertEqual(note.created, aware_datetime(2010, 4, 3, 20, 5))

        request._raw_post_data = request._body = '{"content": "The cat is gone again. I think it was the rabbits that ate him this time."}'

        resp = resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Note.objects.count(), 6)
        new_note = Note.objects.get(pk=1)
        self.assertEqual(new_note.content, u'The cat is gone again. I think it was the rabbits that ate him this time.')

        always_resource = AlwaysDataNoteResourceUseIn()
        request._raw_post_data = request._body = '{"content": "Wait, now the cat is back."}'
        resp = always_resource.patch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 202)
        data = json.loads(resp.content.decode('utf-8'))
        self.assertTrue("id" in data)
        self.assertEqual(data["id"], 1)
        self.assertTrue("author" in data)
        self.assertFalse("constant" in data)
        self.assertTrue("content" in data)
        self.assertEqual(data["content"], u'Wait, now the cat is back.')
        self.assertTrue("resource_uri" in data)
        self.assertTrue("title" in data)
        self.assertTrue("is_active" in data)

    def test_dispatch_list(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]}')

    def test_dispatch_detail(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.dispatch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')

    def test_dispatch(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 4}, "objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]}')

        resp = resource.dispatch('detail', request, pk=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')

        # Check for an override.
        request.META = {
            'HTTP_X_HTTP_METHOD_OVERRIDE': 'PATCH',
        }
        request._read_started = False
        request._raw_post_data = request._body = '{"title": "Super-duper override ACTIVATE!"}'
        resp = resource.dispatch('detail', request, pk=1)
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.content.decode('utf-8'), '')
        self.assertEqual(Note.objects.get(pk=1).title, u'Super-duper override ACTIVATE!')

    def test_build_bundle(self):
        resource = NoteResource()

        unpopulated_bundle = resource.build_bundle()
        self.assertTrue(isinstance(unpopulated_bundle, Bundle))
        self.assertEqual(unpopulated_bundle.data, {})

        populated_bundle = resource.build_bundle(data={'title': 'Foo'})
        self.assertTrue(isinstance(populated_bundle, Bundle))
        self.assertEqual(populated_bundle.data, {'title': 'Foo'})

        req = HttpRequest()
        req.GET = {'foo': 'bar'}
        populated_bundle_with_request = resource.build_bundle(data={'title': 'Foo'}, request=req)
        self.assertTrue(isinstance(populated_bundle_with_request, Bundle))
        self.assertEqual(populated_bundle_with_request.data, {'title': 'Foo'})
        self.assertEqual(populated_bundle_with_request.request.GET['foo'], 'bar')

    def test_obj_get_list(self):
        resource = NoteResource()
        base_bundle = Bundle()

        object_list = resource.obj_get_list(base_bundle)
        self.assertEqual(len(object_list), 4)
        self.assertEqual(object_list[0].title, u'First Post!')

        notes = NoteResource().obj_get_list(base_bundle)
        self.assertEqual(len(notes), 4)
        self.assertEqual(notes[0].is_active, True)
        self.assertEqual(notes[0].title, u'First Post!')
        self.assertEqual(notes[1].is_active, True)
        self.assertEqual(notes[1].title, u'Another Post')
        self.assertEqual(notes[2].is_active, True)
        self.assertEqual(notes[2].title, u'Recent Volcanic Activity.')
        self.assertEqual(notes[3].is_active, True)
        self.assertEqual(notes[3].title, u"Granny's Gone")

        customs = VeryCustomNoteResource().obj_get_list(base_bundle)
        self.assertEqual(len(customs), 6)
        self.assertEqual(customs[0].is_active, True)
        self.assertEqual(customs[0].title, u'First Post!')
        self.assertEqual(customs[0].author.username, u'johndoe')
        self.assertEqual(customs[1].is_active, True)
        self.assertEqual(customs[1].title, u'Another Post')
        self.assertEqual(customs[1].author.username, u'johndoe')
        self.assertEqual(customs[2].is_active, False)
        self.assertEqual(customs[2].title, u'Hello World!')
        self.assertEqual(customs[2].author.username, u'janedoe')
        self.assertEqual(customs[3].is_active, True)
        self.assertEqual(customs[3].title, u'Recent Volcanic Activity.')
        self.assertEqual(customs[3].author.username, u'janedoe')
        self.assertEqual(customs[4].is_active, False)
        self.assertEqual(customs[4].title, u'My favorite new show')
        self.assertEqual(customs[4].author.username, u'johndoe')
        self.assertEqual(customs[5].is_active, True)
        self.assertEqual(customs[5].title, u"Granny's Gone")
        self.assertEqual(customs[5].author.username, u'janedoe')

        # Ensure filtering by request params works.
        mock_request = MockRequest()
        mock_request.GET['title'] = u"Granny's Gone"
        base_bundle.request = mock_request
        notes = NoteResource().obj_get_list(bundle=base_bundle)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, u"Granny's Gone")

        # Ensure kwargs override request params.
        mock_request = MockRequest()
        mock_request.GET['title'] = u"Granny's Gone"
        base_bundle.request = mock_request
        notes = NoteResource().obj_get_list(bundle=base_bundle, title='Recent Volcanic Activity.')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, u'Recent Volcanic Activity.')

    def test_apply_filters(self):
        nr = NoteResource()
        mock_request = MockRequest()

        # No filters.
        notes = nr.apply_filters(mock_request, {})
        self.assertEqual(len(notes), 4)

        filters = {
            'title': u"Granny's Gone"
        }
        notes = nr.apply_filters(mock_request, filters)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, u"Granny's Gone")

        filters = {
            'title__icontains': u"post",
            'created__lte': datetime.date(2010, 6, 30),
        }
        notes = nr.apply_filters(mock_request, filters)
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].title, u'First Post!')
        self.assertEqual(notes[1].title, u'Another Post')

    def test_obj_get(self):
        resource = NoteResource()
        base_bundle = Bundle()

        obj = resource.obj_get(base_bundle, pk=1)
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj.title, u'First Post!')

        # Test non-pk gets.
        obj = resource.obj_get(base_bundle, slug='another-post')
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj.title, u'Another Post')

        note = NoteResource()
        note_obj = note.obj_get(base_bundle, pk=1)
        self.assertEqual(note_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(note_obj.created, aware_datetime(2010, 3, 30, 20, 5))
        self.assertEqual(note_obj.is_active, True)
        self.assertEqual(note_obj.slug, u'first-post')
        self.assertEqual(note_obj.title, u'First Post!')
        self.assertEqual(note_obj.updated, aware_datetime(2010, 3, 30, 20, 5))

        custom = VeryCustomNoteResource()
        custom_obj = custom.obj_get(base_bundle, pk=1)
        self.assertEqual(custom_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(custom_obj.created, aware_datetime(2010, 3, 30, 20, 5))
        self.assertEqual(custom_obj.is_active, True)
        self.assertEqual(custom_obj.author.username, u'johndoe')
        self.assertEqual(custom_obj.title, u'First Post!')

        related = RelatedNoteResource()
        related_obj = related.obj_get(base_bundle, pk=1)
        self.assertEqual(related_obj.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(related_obj.created, aware_datetime(2010, 3, 30, 20, 5))
        self.assertEqual(related_obj.is_active, True)
        self.assertEqual(related_obj.author.username, u'johndoe')
        self.assertEqual(related_obj.title, u'First Post!')
        self.assertEqual(list(related_obj.subjects.values_list('id', flat=True)), [1, 2])

    def test_obj_get_across_related(self):
        new_user = User.objects.create(username='foo')
        new_note = Note.objects.create(author=new_user)

        class RelatedFilterNoteResource(NoteResource):
            author = fields.ToOneField(UserResource, 'author')

            class Meta(NoteResource.Meta):
                filtering = {
                    'author': ALL_WITH_RELATIONS,
                }

        resource = RelatedFilterNoteResource()
        base_bundle = Bundle()

        obj = resource.obj_get(base_bundle, author__username=new_user.username)
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj, new_note)

    def test_uri_fields(self):
        with_abs_url = WithAbsoluteURLNoteResource()
        base_bundle = Bundle()
        with_abs_url_obj = with_abs_url.obj_get(base_bundle, pk=1)

        with_abs_url_bundle = with_abs_url.build_bundle(obj=with_abs_url_obj)
        abs_bundle = with_abs_url.full_dehydrate(with_abs_url_bundle)
        self.assertEqual(abs_bundle.data['resource_uri'], '/api/v1/withabsoluteurlnote/1/')
        self.assertEqual(abs_bundle.data['absolute_url'], u'/some/fake/path/1/')

    def test_jsonp_validation(self):
        resource = NoteResource()

        # invalid JSONP callback should return Http400
        request = HttpRequest()
        request.GET = {'format': 'jsonp', 'callback': '()'}
        request.method = 'GET'
        with self.assertRaises(BadRequest):
            resp = resource.dispatch_detail(request, pk=1)

        # Try again with ``wrap_view`` for sanity.
        resp = resource.wrap_view('dispatch_detail')(request, pk=1)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(force_str(resp.content), '{"error": "JSONP callback name is invalid."}')
        self.assertEqual(resp['content-type'], 'application/json')

        # valid JSONP callback should work
        request = HttpRequest()
        request.GET = {'format': 'jsonp', 'callback': 'myCallback'}
        request.method = 'GET'
        resp = resource.dispatch_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)

    def test_get_schema(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Patch the ``created/updated`` defaults for testability.
        with patch.object(resource.fields['created'], '_default', new=aware_datetime(2011, 9, 24, 0, 2)),\
                patch.object(resource.fields['updated'], '_default', new=aware_datetime(2011, 9, 24, 0, 2)):
            resp = resource.get_schema(request)

        self.assertEqual(resp.status_code, 200)

        expected_schema = {
            "allowed_detail_http_methods": ["get", "post", "put", "delete", "patch"],
            "allowed_list_http_methods": ["get", "post", "put", "delete", "patch"],
            "default_format": "application/json",
            "default_limit": 20,
            "fields": {
                "content": {
                    "blank": True,
                    "default": "",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'content',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "created": {
                    "blank": False,
                    "default": "2011-09-24T00:02:00",
                    "help_text": "A date & time as a string. Ex: \"2010-11-10T03:07:43\"",
                    "verbose_name": 'created',
                    "nullable": False,
                    "readonly": False,
                    "type": "datetime",
                    "unique": False,
                    "primary_key": False
                },
                "id": {
                    "blank": True,
                    "default": "",
                    "help_text": "Integer data. Ex: 2673",
                    "verbose_name": 'ID',
                    "nullable": False,
                    "readonly": False,
                    "type": "integer",
                    "unique": True,
                    "primary_key": True
                },
                "is_active": {
                    "blank": True,
                    "default": True,
                    "help_text": "Boolean data. Ex: True",
                    "verbose_name": 'is active',
                    "nullable": False,
                    "readonly": False,
                    "type": "boolean",
                    "unique": False,
                    "primary_key": False
                },
                "resource_uri": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'resource uri',
                    "nullable": False,
                    "readonly": True,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "slug": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'slug',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "title": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'The Title',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "updated": {
                    "blank": False,
                    "default": "2011-09-24T00:02:00",
                    "help_text": "A date & time as a string. Ex: \"2010-11-10T03:07:43\"",
                    "verbose_name": 'updated',
                    "nullable": False,
                    "readonly": False,
                    "type": "datetime",
                    "unique": False,
                    "primary_key": False
                }
            },
            "filtering": {
                "content": ["startswith", "exact"],
                "slug": ["exact"],
                "created": 1,
                "title": 1
            },
            "ordering": ["title", "slug", "resource_uri"],
        }

        schema = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(schema, expected_schema)

    def test_get_schema_with_related(self):
        resource = RelatedNoteResource()

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Patch the ``created/updated`` defaults for testability.
        with patch.object(resource.fields['created'], '_default', new=aware_datetime(2011, 9, 24, 0, 2)):
            resp = resource.get_schema(request)

        self.assertEqual(resp.status_code, 200)

        expected_schema = {
            "allowed_detail_http_methods": ["get", "post", "put", "delete", "patch"],
            "allowed_list_http_methods": ["get", "post", "put", "delete", "patch"],
            "default_format": "application/json",
            "default_limit": 20,
            "fields": {
                "content": {
                    "blank": True,
                    "default": "",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'content',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "created": {
                    "blank": False,
                    "default": "2011-09-24T00:02:00",
                    "help_text": "A date & time as a string. Ex: \"2010-11-10T03:07:43\"",
                    "verbose_name": 'created',
                    "nullable": False,
                    "readonly": False,
                    "type": "datetime",
                    "unique": False,
                    "primary_key": False
                },
                "is_active": {
                    "blank": True,
                    "default": True,
                    "help_text": "Boolean data. Ex: True",
                    "verbose_name": 'is active',
                    "nullable": False,
                    "readonly": False,
                    "type": "boolean",
                    "unique": False,
                    "primary_key": False
                },
                "resource_uri": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'resource uri',
                    "nullable": False,
                    "readonly": True,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "slug": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'slug',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "title": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'The Title',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                'author': {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": 'A single related resource. Can be either a URI or set of nested resource data.',
                    "verbose_name": 'The Author',
                    "readonly": False,
                    "nullable": False,
                    "type": 'related',
                    "unique": False,
                    "primary_key": False,
                    "related_schema": '/api/v1/user/schema/',
                    "related_type": 'to_one'
                },
                'subjects': {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": 'Many related resources. Can be either a list of URIs or list of individually nested resource data.',
                    "verbose_name": 'subjects',
                    "readonly": False,
                    "nullable": False,
                    "type": 'related',
                    "unique": False,
                    "primary_key": False,
                    "related_schema": '/api/v1/subjects/schema/',
                    "related_type": 'to_many'
                }
            },
            'default_format': 'application/json',
            'filtering': {
                'author': ALL,
                'subjects': ALL_WITH_RELATIONS,
            },
        }

        schema = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(schema, expected_schema)

    def test_get_schema_with_related_resource_not_in_urls(self):
        """
        Test case for #1439. Need to handle schemas for related resources that
        aren't in any urlconfs.
        """
        class GhostResource(Resource):
            foo = fields.CharField()

            class Meta:
                object_class = object

        class CustomRelatedNoteResource(RelatedNoteResource):
            ghost = fields.ToOneField(GhostResource, 'ghost')

            Meta = RelatedNoteResource.Meta

        resource = CustomRelatedNoteResource()

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Patch the ``created/updated`` defaults for testability.
        with patch.object(resource.fields['created'], '_default', new=aware_datetime(2011, 9, 24, 0, 2)):
            resp = resource.get_schema(request)

        self.assertEqual(resp.status_code, 200)

        expected_schema = {
            "allowed_detail_http_methods": ["get", "post", "put", "delete", "patch"],
            "allowed_list_http_methods": ["get", "post", "put", "delete", "patch"],
            "default_format": "application/json",
            "default_limit": 20,
            "fields": {
                "content": {
                    "blank": True,
                    "default": "",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'content',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "created": {
                    "blank": False,
                    "default": "2011-09-24T00:02:00",
                    "help_text": "A date & time as a string. Ex: \"2010-11-10T03:07:43\"",
                    "verbose_name": 'created',
                    "nullable": False,
                    "readonly": False,
                    "type": "datetime",
                    "unique": False,
                    "primary_key": False
                },
                "is_active": {
                    "blank": True,
                    "default": True,
                    "help_text": "Boolean data. Ex: True",
                    "verbose_name": 'is active',
                    "nullable": False,
                    "readonly": False,
                    "type": "boolean",
                    "unique": False,
                    "primary_key": False
                },
                "resource_uri": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'resource uri',
                    "nullable": False,
                    "readonly": True,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "slug": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'slug',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                "title": {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": "Unicode string data. Ex: \"Hello World\"",
                    "verbose_name": 'The Title',
                    "nullable": False,
                    "readonly": False,
                    "type": "string",
                    "unique": False,
                    "primary_key": False
                },
                'ghost': {
                    "blank": False,
                    "default": "No default provided.",
                    "help_text": 'A single related resource. Can be either a URI or set of nested resource data.',
                    "verbose_name": 'ghost',
                    "readonly": False,
                    "nullable": False,
                    "type": 'related',
                    "unique": False,
                    "primary_key": False,
                    "related_schema": '',
                    "related_type": 'to_one'
                }
            },
            'default_format': 'application/json',
            'filtering': {
                'author': ALL,
                'subjects': ALL_WITH_RELATIONS,
            },
        }

        schema = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(schema['fields'], expected_schema['fields'])

    @patch('tastypie.resources.ModelResource.obj_get_list', side_effect=NotImplementedError)
    def test_get_multiple_without_queryset(self, obj_get_list_mock):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.get_multiple(request, pk_list='1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}]}')

        resp = resource.get_multiple(request, pk_list='1;2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}]}')

        resp = resource.get_multiple(request, pk_list='2;3')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"not_found": ["3"], "objects": [{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}]}')

        resp = resource.get_multiple(request, pk_list='1;2;4;6')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]}')

    def test_get_multiple(self):
        resource = NoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.get_multiple(request, pk_list='1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}]}')

        with self.assertNumQueries(1):
            resp = resource.get_multiple(request, pk_list='1;2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}]}')

        with self.assertNumQueries(1):
            resp = resource.get_multiple(request, pk_list='2;3')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"not_found": ["3"], "objects": [{"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}]}')

        with self.assertNumQueries(1):
            resp = resource.get_multiple(request, pk_list='1;2;4;6')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"objects": [{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}, {"content": "The dog ate my cat today. He looks seriously uncomfortable.", "created": "2010-03-31T20:05:00", "id": 2, "is_active": true, "resource_uri": "/api/v1/notes/2/", "slug": "another-post", "title": "Another Post", "updated": "2010-03-31T20:05:00"}, {"content": "My neighborhood\'s been kinda weird lately, especially after the lava flow took out the corner store. Granny can hardly outrun the magma with her walker.", "created": "2010-04-01T20:05:00", "id": 4, "is_active": true, "resource_uri": "/api/v1/notes/4/", "slug": "recent-volcanic-activity", "title": "Recent Volcanic Activity.", "updated": "2010-04-01T20:05:00"}, {"content": "Man, the second eruption came on fast. Granny didn\'t have a chance. On the upshot, I was able to save her walker and I got a cool shawl out of the deal!", "created": "2010-04-02T10:05:00", "id": 6, "is_active": true, "resource_uri": "/api/v1/notes/6/", "slug": "grannys-gone", "title": "Granny\'s Gone", "updated": "2010-04-02T10:05:00"}]}')

    def test_get_multiple_use_in(self):
        resource = AlwaysDataNoteResourceUseIn()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        resp = resource.get_multiple(request, pk_list='1')
        self.assertEqual(resp.status_code, 200)
        content = json.loads(resp.content.decode('utf-8'))
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

        resp = resource.get_multiple(request, pk_list='1;2')
        self.assertEqual(resp.status_code, 200)
        content = json.loads(resp.content.decode('utf-8'))
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

        resp = resource.get_multiple(request, pk_list='2;3')
        self.assertEqual(resp.status_code, 200)
        content = json.loads(resp.content.decode('utf-8'))
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

        resp = resource.get_multiple(request, pk_list='1;2;4;6')
        self.assertEqual(resp.status_code, 200)
        content = json.loads(resp.content.decode('utf-8'))
        for note in content['objects']:
            self.assertIn('constant', note)
            self.assertNotIn('author', note)

    @patch('tastypie.throttle.time')
    @override_settings(DEBUG=False)
    def test_check_bool_throttling(self, mocked_time):
        mocked_time.time.return_value = time.time()

        resource = ThrottledNoteResource()
        _orginal_throttle = resource._meta.throttle

        class BoolThrottle(resource._meta.throttle.__class__):
            def should_be_throttled(self, *args, **kwargs):
                ret = super(BoolThrottle, self).should_be_throttled(*args, **kwargs)
                if ret:
                    return True
                return False
        resource._meta.throttle = BoolThrottle(
            throttle_at=resource._meta.throttle.throttle_at,
            timeframe=resource._meta.throttle.timeframe,
            expiration=resource._meta.throttle.expiration
        )

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 1)

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertNotIn('Retry-After', e.response)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertNotIn('Retry-After', e.response)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Check the ``wrap_view``.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 429)
        self.assertNotIn('Retry-After', resp)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        resource._meta.throttle = _orginal_throttle

    @patch('tastypie.throttle.time')
    @override_settings(DEBUG=False)
    def test_check_int_throttling(self, mocked_time):
        mocked_time.time.return_value = time.time()

        resource = ThrottledNoteResource()
        _orginal_throttle = resource._meta.throttle
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 1)

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], '5')
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], '5')
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Check the ``wrap_view``.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp['Retry-After'], '5')
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        resource._meta.throttle = _orginal_throttle

    @patch('tastypie.throttle.time')
    @override_settings(DEBUG=False)
    def test_check_datetime_throttling(self, mocked_time):

        retry_after = datetime.datetime(year=2014, month=8, day=8, hour=8, minute=55, tzinfo=timezone.utc)
        mocked_time.time.return_value = mktime(retry_after.timetuple())
        retry_after_str = 'Fri, 08 Aug 2014 08:55:00 GMT'

        resource = ThrottledNoteResource()
        _orginal_throttle = resource._meta.throttle

        class DatetimeThrottle(resource._meta.throttle.__class__):
            def should_be_throttled(self, *args, **kwargs):
                ret = super(DatetimeThrottle, self).should_be_throttled(*args, **kwargs)
                if ret:
                    return retry_after
                return False
        resource._meta.throttle = DatetimeThrottle(
            throttle_at=resource._meta.throttle.throttle_at,
            timeframe=resource._meta.throttle.timeframe,
            expiration=resource._meta.throttle.expiration
        )

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 1)

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Check the ``wrap_view``.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        resource._meta.throttle = _orginal_throttle

    @patch('tastypie.throttle.time')
    @override_settings(DEBUG=False, USE_TZ=False)
    def test_check_datetime_throttling_notz(self, mocked_time):

        retry_after = datetime.datetime(year=2014, month=8, day=8, hour=8, minute=55, tzinfo=timezone.utc)
        mocked_time.time.return_value = mktime(retry_after.timetuple())
        retry_after_str = 'Fri, 08 Aug 2014 08:55:00 GMT'

        resource = ThrottledNoteResource()
        _orginal_throttle = resource._meta.throttle

        class DatetimeThrottle(resource._meta.throttle.__class__):
            def should_be_throttled(self, *args, **kwargs):
                ret = super(DatetimeThrottle, self).should_be_throttled(*args, **kwargs)
                if ret:
                    return retry_after
                return False
        resource._meta.throttle = DatetimeThrottle(
            throttle_at=resource._meta.throttle.throttle_at,
            timeframe=resource._meta.throttle.timeframe,
            expiration=resource._meta.throttle.expiration
        )

        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 1)

        # Not throttled.
        resp = resource.dispatch('list', request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Throttled.
        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch('list', request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 429)
        self.assertEqual(e.response['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        # Check the ``wrap_view``.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp['Retry-After'], retry_after_str)
        self.assertEqual(len(cache.get('noaddr_nohost_accesses')), 2)

        resource._meta.throttle = _orginal_throttle

    def test_generate_cache_key(self):
        resource = NoteResource(api_name='v1')
        self.assertEqual(resource.generate_cache_key(), 'v1:notes::')
        self.assertEqual(resource.generate_cache_key('abc', '123'), 'v1:notes:abc:123:')
        self.assertEqual(resource.generate_cache_key(foo='bar', moof='baz'), 'v1:notes::foo=bar:moof=baz')
        self.assertEqual(resource.generate_cache_key('abc', '123', foo='bar', moof='baz'), 'v1:notes:abc:123:foo=bar:moof=baz')

    def test_cached_fetch_list(self):
        resource = NoteResource()
        base_bundle = Bundle()

        object_list = resource.cached_obj_get_list(base_bundle)
        self.assertEqual(len(object_list), 4)
        self.assertEqual(object_list[0].title, u'First Post!')

    def test_cached_fetch_detail(self):
        resource = NoteResource()
        base_bundle = Bundle()

        obj = resource.cached_obj_get(base_bundle, pk=1)
        self.assertTrue(isinstance(obj, Note))
        self.assertEqual(obj.title, u'First Post!')

    def test_configuration(self):
        note = NoteResource()
        self.assertEqual(len(note.fields), 8)
        self.assertEqual(sorted(note.fields.keys()), ['content', 'created', 'id', 'is_active', 'resource_uri', 'slug', 'title', 'updated'])
        self.assertEqual(note.fields['content'].default, '')

        custom = VeryCustomNoteResource()
        self.assertEqual(len(custom.fields), 7)
        self.assertEqual(sorted(custom.fields.keys()), ['author', 'constant', 'content', 'created', 'is_active', 'resource_uri', 'title'])

        no_uri = NoUriNoteResource()
        self.assertEqual(len(no_uri.fields), 7)
        self.assertEqual(sorted(no_uri.fields.keys()), ['content', 'created', 'id', 'is_active', 'slug', 'title', 'updated'])

        with_abs_url = WithAbsoluteURLNoteResource()
        self.assertEqual(len(with_abs_url.fields), 9)
        self.assertEqual(sorted(with_abs_url.fields.keys()), ['absolute_url', 'content', 'created', 'id', 'is_active', 'resource_uri', 'slug', 'title', 'updated'])

    def test_obj_delete_list_custom_qs(self):
        self.assertEqual(len(Note.objects.all()), 6)
        base_bundle = Bundle()
        NoteResource().obj_delete_list(base_bundle)
        self.assertEqual(len(Note.objects.all()), 2)

    def test_obj_delete_list_basic_qs(self):
        self.assertEqual(len(Note.objects.all()), 6)
        base_bundle = Bundle()
        VeryCustomNoteResource().obj_delete_list(base_bundle)
        self.assertEqual(len(Note.objects.all()), 0)

    def test_obj_delete_list_non_queryset(self):
        class NonQuerysetNoteResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()

            def authorized_delete_list(self, object_list, bundle):
                return tuple(object_list[:2])

        request = HttpRequest()
        request.method = 'DELETE'
        self.assertEqual(len(Note.objects.all()), 6)
        # This is a regression. Used to fail miserably.
        NonQuerysetNoteResource().delete_list(request=request)
        self.assertEqual(len(Note.objects.all()), 4)

    def test_obj_delete_list_filtered(self):
        self.assertEqual(Note.objects.all().count(), 6)

        note_to_delete = Note.objects.filter(is_active=True)[0]

        request = HttpRequest()
        request.method = 'DELETE'
        request.GET = {'slug': str(note_to_delete.slug)}
        NoteResource().delete_list(request=request)
        self.assertEqual(len(Note.objects.all()), 5)

    def test_obj_create(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        bundle = Bundle(data={
            'title': "A new post!",
            'slug': "a-new-post",
            'content': "Testing, 1, 2, 3!",
            'is_active': True
        })
        note.obj_create(bundle)
        self.assertEqual(Note.objects.all().count(), 7)
        latest = Note.objects.get(slug='a-new-post')
        self.assertEqual(latest.title, u"A new post!")
        self.assertEqual(latest.slug, u'a-new-post')
        self.assertEqual(latest.content, u'Testing, 1, 2, 3!')
        self.assertEqual(latest.is_active, True)

        self.assertEqual(Note.objects.all().count(), 7)
        note = RelatedNoteResource()
        related_bundle = Bundle(data={
            'title': "Yet another new post!",
            'slug': "yet-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/user/1/',
            'subjects': ['/api/v1/subjects/2/'],
        })
        note.obj_create(related_bundle)
        self.assertEqual(Note.objects.all().count(), 8)
        latest = Note.objects.get(slug='yet-another-new-post')
        self.assertEqual(latest.title, u"Yet another new post!")
        self.assertEqual(latest.slug, u'yet-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'johndoe')
        self.assertEqual(latest.subjects.all().count(), 1)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [2])

        self.assertEqual(Note.objects.all().count(), 8)
        note = AnotherRelatedNoteResource()
        related_bundle = Bundle(data={
            'title': "Yet another another new post!",
            'slug': "yet-another-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/user/1/',
            'subjects': [{
                'name': 'helloworld',
                'url': 'http://example.com',
                'created': '2010-05-20 14:22:00',
            }],
        })
        note.obj_create(related_bundle)
        self.assertEqual(Note.objects.all().count(), 9)
        latest = Note.objects.get(slug='yet-another-another-new-post')
        self.assertEqual(latest.title, u"Yet another another new post!")
        self.assertEqual(latest.slug, u'yet-another-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'johndoe')
        self.assertEqual(latest.subjects.all().count(), 1)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [3])

        self.assertEqual(Note.objects.all().count(), 9)
        self.assertEqual(User.objects.filter(username='snerble').count(), 0)
        note = YetAnotherRelatedNoteResource()
        related_bundle = Bundle(data={
            'title': "Yet yet another another new post!",
            'slug': "yet-yet-another-another-new-post",
            'content': "WHOA!!!",
            'is_active': True,
            'author': {
                'username': 'snerble',
                'password': 'hunter42',
            },
            'subjects': [],
        })
        note.obj_create(related_bundle)
        self.assertEqual(Note.objects.all().count(), 10)
        latest = Note.objects.get(slug='yet-yet-another-another-new-post')
        self.assertEqual(latest.title, u"Yet yet another another new post!")
        self.assertEqual(latest.slug, u'yet-yet-another-another-new-post')
        self.assertEqual(latest.content, u'WHOA!!!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'snerble')
        self.assertEqual(latest.subjects.all().count(), 0)

        note = RequiredFKNoteResource()
        related_bundle = Bundle(data={
            'slug': 'note-with-editor',
            'editor': {
                'username': 'zeus',
                'password': 'apollo',
            },
        })
        note.obj_create(related_bundle)
        latest = NoteWithEditor.objects.get(slug='note-with-editor')
        self.assertEqual(latest.editor.username, u'zeus')

    def test_obj_create_full_hydrate_on_create_authorization(self):
        cr = CounterCreateDetailResource()
        counter_bundle = cr.build_bundle(data={
            "name": "About",
            "slug": "about",
        }, obj=Counter())
        cr.obj_create(counter_bundle)

        self.assertEquals(counter_bundle._create_auth_call_count, 1)
        self.assertEquals(counter_bundle.obj.name, "About")
        self.assertEquals(counter_bundle.obj.slug, "about")

    def test_obj_update(self):
        self.assertEqual(Note.objects.all().count(), 6)

        note = NoteResource()
        base_bundle = Bundle()
        note_obj = note.obj_get(base_bundle, pk=1)
        note_bundle = note.build_bundle(obj=note_obj)
        note_bundle = note.full_dehydrate(note_bundle)
        note_bundle.data['title'] = 'Whee!'
        with self.assertNumQueries(1):
            note.obj_update(note_bundle, pk=1)
        self.assertEqual(Note.objects.all().count(), 6)
        numero_uno = Note.objects.get(pk=1)
        self.assertEqual(numero_uno.title, u'Whee!')
        self.assertEqual(numero_uno.slug, u'first-post')
        self.assertEqual(numero_uno.content, u'This is my very first post using my shiny new API. Pretty sweet, huh?')
        self.assertEqual(numero_uno.is_active, True)

        # same setup as above, just need to test with '1' as the pk (str
        # instead of int)
        note = NoteResource()
        base_bundle = Bundle()
        note_obj = note.obj_get(base_bundle, pk=1)
        note_bundle = note.build_bundle(obj=note_obj)
        note_bundle = note.full_dehydrate(note_bundle)
        note_bundle.data['title'] = 'Whee!'
        with self.assertNumQueries(1):
            note.obj_update(note_bundle, pk='1')
        self.assertEqual(Note.objects.all().count(), 6)

        self.assertEqual(Note.objects.all().count(), 6)
        note = RelatedNoteResource()
        related_obj = note.obj_get(base_bundle, pk=1)
        related_bundle = Bundle(obj=related_obj, data={
            'title': "Yet another new post!",
            'slug': "yet-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/user/2/',
            'subjects': ['/api/v1/subjects/2/', '/api/v1/subjects/1/'],
        })
        note.obj_update(related_bundle, pk=1)
        self.assertEqual(Note.objects.all().count(), 6)
        latest = Note.objects.get(slug='yet-another-new-post')
        self.assertEqual(latest.title, u"Yet another new post!")
        self.assertEqual(latest.slug, u'yet-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'janedoe')
        self.assertEqual(latest.subjects.all().count(), 2)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [1, 2])

        self.assertEqual(Note.objects.all().count(), 6)
        note = AnotherRelatedNoteResource()
        related_obj = note.obj_get(base_bundle, pk=1)
        related_bundle = Bundle(data={
            'title': "Yet another another new post!",
            'slug': "yet-another-another-new-post",
            'content': "WHEEEEEE!",
            'is_active': True,
            'author': '/api/v1/user/1/',
            'subjects': [{
                'name': 'helloworld',
                'url': 'http://example.com',
                'created': '2010-05-20 14:22:00',
            }],
        })
        note.obj_update(related_bundle, pk=1)
        self.assertEqual(Note.objects.all().count(), 6)
        latest = Note.objects.get(slug='yet-another-another-new-post')
        self.assertEqual(latest.title, u"Yet another another new post!")
        self.assertEqual(latest.slug, u'yet-another-another-new-post')
        self.assertEqual(latest.content, u'WHEEEEEE!')
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.author.username, u'johndoe')
        self.assertEqual(latest.subjects.all().count(), 1)
        self.assertEqual([sub.id for sub in latest.subjects.all()], [3])

        # Fix non-native types (like datetimes) during attempted hydration.
        # This ensures that handing the wrong type should get coerced to the
        # right thing.
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        note_obj = note.obj_get(base_bundle, pk=1)
        self.assertEqual(note_obj.title, u'Yet another another new post!')
        self.assertEqual(note_obj.created, aware_datetime(2010, 3, 30, 20, 5))
        note_bundle = note.build_bundle(obj=note_obj)
        note_bundle = note.full_dehydrate(note_bundle)
        note_bundle.data['title'] = 'OMGOMGOMGOMG!'
        note_bundle.data['created'] = aware_datetime(2011, 11, 23, 1, 0, 0)
        note.obj_update(note_bundle, pk=1, created='2010-03-30T20:05:00')
        self.assertEqual(Note.objects.all().count(), 6)
        numero_uno = Note.objects.get(pk=1)
        self.assertEqual(numero_uno.title, u'OMGOMGOMGOMG!')
        self.assertEqual(numero_uno.slug, u'yet-another-another-new-post')
        self.assertEqual(numero_uno.content, u'WHEEEEEE!')
        self.assertEqual(numero_uno.created, aware_datetime(2011, 11, 23, 1, 0))

        # Now try a lookup that should fail.
        note = NoteResource()
        note_bundle = note.build_bundle(data={
            "author": "/api/v1/user/1/",
            "title": "Something something Post!",
            "slug": "something-something-post",
            "content": "Stock post content.",
            "is_active": True,
            "created": "2011-03-30 20:05:00",
            "updated": "2011-03-30 20:05:00"
        })
        self.assertRaises(NotFound, note.obj_update, note_bundle, pk=1, created='2010-03-31T20:05:00')
        self.assertEqual(Note.objects.all().count(), 6)

        # Assign based on the ``request.user``, which helps ensure that
        # the correct ``request`` is being passed along.
        request = HttpRequest()
        request.user = User.objects.get(username='johndoe')
        base_bundle.request = request
        self.assertEqual(AlwaysUserNoteResource().get_object_list(request).count(), 2)
        note = AlwaysUserNoteResource()
        note_obj = note.obj_get(base_bundle, pk=1)
        note_bundle = note.build_bundle(obj=note_obj)
        note_bundle = note.full_dehydrate(note_bundle)
        note_bundle.data['title'] = 'Whee!'
        note_bundle.request = request
        note.obj_update(note_bundle, pk=1)
        self.assertEqual(Note.objects.all().count(), 6)
        numero_uno = Note.objects.get(pk=1)
        self.assertEqual(numero_uno.title, u'Whee!')
        self.assertEqual(numero_uno.slug, u'yet-another-another-new-post')
        self.assertEqual(numero_uno.content, u'WHEEEEEE!')
        self.assertEqual(numero_uno.is_active, True)
        self.assertEqual(numero_uno.author.pk, request.user.pk)

    def test_obj_update_single_hydrate(self):
        counter = Counter.objects.get(pk=1)

        self.assertEqual(counter.count, 1)

        cr = CounterResource()
        counter_bundle = cr.build_bundle(data={
            "pk": counter.pk,
            "name": "Signups",
            "slug": "signups",
        })
        cr.obj_update(counter_bundle, pk=1)

        self.assertEqual(Counter.objects.all().count(), 2)
        counter = Counter.objects.get(pk=1)
        self.assertEqual(counter.count, 1)

    def test_obj_update_full_hydrate_on_update_authorization(self):
        counter = Counter.objects.get(pk=1)

        cr = CounterUpdateDetailResource()
        counter_bundle = cr.build_bundle(data={
            "pk": counter.pk,
            "name": "Signups",
            "slug": "signups",
        }, obj=Counter())
        cr.obj_update(counter_bundle, pk=1)

        counter = Counter.objects.get(pk=1)
        self.assertEquals(counter_bundle._update_auth_call_count, 1)
        self.assertEquals(counter_bundle.obj.name, "Signups")
        self.assertEquals(counter_bundle.obj.slug, "signups")

    def test_lookup_kwargs_with_identifiers__field_without_attr(self):
        """
        Verify PR #942 fixed.
        """
        class FieldWithoutAttributeNoteResource(NoteResource):
            noattrfield = fields.CharField()
        note = FieldWithoutAttributeNoteResource()
        note_bundle = note.build_bundle()
        note_bundle.data['title'] = 'Whee!'

        # need to use ordered dict to make sure 'noattrfield' comes before
        # 'id', otherwise the value of 'id' gets used for 'noattrfield'.
        kwargs = OrderedDict([('noattrfield', 'foo'), ('id', 1)])
        lookup_kwargs = note.lookup_kwargs_with_identifiers(note_bundle, kwargs)

        self.assertEqual(lookup_kwargs, {'id': 1})

    def test_obj_delete(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()
        base_bundle = Bundle()
        note.obj_delete(base_bundle, pk=1)
        self.assertEqual(Note.objects.all().count(), 5)
        self.assertRaises(Note.DoesNotExist, Note.objects.get, pk=1)

        # Test non-pk deletes.
        base_bundle = Bundle()
        note.obj_delete(base_bundle, slug='another-post')
        self.assertEqual(Note.objects.all().count(), 4)
        self.assertRaises(Note.DoesNotExist, Note.objects.get, slug='another-post')

    def test_rollback(self):
        self.assertEqual(Note.objects.all().count(), 6)
        note = NoteResource()

        bundles_seen = []
        note.rollback(bundles_seen)
        self.assertEqual(Note.objects.all().count(), 6)

        # The one that exists should be deleted, the others ignored.
        bundles_seen = [Bundle(obj=Note.objects.get(pk=1)), Bundle(obj=Note()), Bundle()]
        note.rollback(bundles_seen)
        self.assertEqual(Note.objects.all().count(), 5)

    def test_is_valid(self):
        # Using the plug.
        note = NoteResource()
        bundle = Bundle(data={})

        note_is_valid = note.is_valid(bundle)
        self.assertTrue(note_is_valid, "Stock 'is_valid' should return True.")

        # An actual form.
        class NoteForm(forms.Form):
            title = forms.CharField(max_length=100)
            slug = forms.CharField(max_length=50)
            content = forms.CharField(required=False, widget=forms.Textarea)
            is_active = forms.BooleanField()

            # Define a custom clean to make sure non-field errors are making it
            # through.
            def clean(self):
                if not self.cleaned_data.get('content', ''):
                    raise forms.ValidationError('Having no content makes for a very boring note.')

                return self.cleaned_data

        class ValidatedNoteResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()
                resource_name = 'validated'
                validation = FormValidation(form_class=NoteForm)

        class ValidatedXMLNoteResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()
                resource_name = 'validated'
                validation = FormValidation(form_class=NoteForm)
                default_format = 'application/xml'

        validated = ValidatedNoteResource()

        # Test empty data.
        bundle = Bundle(data={})
        self.assertFalse(validated.is_valid(bundle))
        self.assertEqual(bundle.errors, {'validated': {'is_active': [u'This field is required.'], 'slug': [u'This field is required.'], '__all__': [u'Having no content makes for a very boring note.'], 'title': [u'This field is required.']}})

        # Test something that fails validation.
        bundle = Bundle(data={
            'title': 123,
            'slug': '123456789012345678901234567890123456789012345678901234567890',
            'content': '',
            'is_active': True,
        })
        self.assertFalse(validated.is_valid(bundle))
        self.assertEqual(bundle.errors, {'validated': {'slug': [u'Ensure this value has at most 50 characters (it has 60).'], '__all__': [u'Having no content makes for a very boring note.']}})

        # Test something that passes validation.
        bundle = Bundle(data={
            'title': 'Test Content',
            'slug': 'test-content',
            'content': "It doesn't get any more awesome than this.",
            'is_active': True,
        })

        self.assertTrue(validated.is_valid(bundle))

    def test_self_referential(self):
        class SelfResource(ModelResource):
            me_baby_me = fields.ToOneField('self', 'parent', null=True)

            class Meta:
                queryset = Note.objects.all()
                resource_name = 'me_baby_me'

        me_baby_me = SelfResource()
        self.assertEqual(len(me_baby_me.fields), 9)
        self.assertEqual(me_baby_me._meta.resource_name, 'me_baby_me')
        self.assertEqual(me_baby_me.fields['me_baby_me'].to, 'self')
        self.assertEqual(me_baby_me.fields['me_baby_me'].to_class, SelfResource)

        class AnotherSelfResource(SelfResource):
            class Meta:
                queryset = Note.objects.all()
                resource_name = 'another_me_baby_me'

        another_me_baby_me = AnotherSelfResource()
        self.assertEqual(len(another_me_baby_me.fields), 9)
        self.assertEqual(another_me_baby_me._meta.resource_name, 'another_me_baby_me')
        self.assertEqual(another_me_baby_me.fields['me_baby_me'].to, 'self')
        self.assertEqual(another_me_baby_me.fields['me_baby_me'].to_class, AnotherSelfResource)

        # make sure these remained the same
        self.assertEqual(len(me_baby_me.fields), 9)
        self.assertEqual(me_baby_me._meta.resource_name, 'me_baby_me')
        self.assertEqual(me_baby_me.fields['me_baby_me'].to, 'self')
        self.assertEqual(me_baby_me.fields['me_baby_me'].to_class, SelfResource)

    def test_subclassing(self):
        class MiniResource(ModelResource):
            abcd = fields.CharField(default='abcd')
            efgh = fields.IntegerField(default=1234)

            class Meta:
                queryset = Note.objects.all()
                resource_name = 'mini'

        mini = MiniResource()
        self.assertEqual(len(mini.fields), 10)
        self.assertEqual(len(mini._meta.queryset.all()), 6)
        self.assertEqual(mini._meta.resource_name, 'mini')

        class AnotherMiniResource(MiniResource):
            ijkl = fields.BooleanField(default=True)

            class Meta:
                queryset = Note.objects.all()
                resource_name = 'anothermini'

        another = AnotherMiniResource()
        self.assertEqual(len(another.fields), 11)
        self.assertEqual(len(another._meta.queryset.all()), 6)
        self.assertEqual(another._meta.resource_name, 'anothermini')

        class YetAnotherMiniResource(MiniResource):
            mnop = fields.FloatField(default=True)

            class Meta:
                queryset = Note.objects.all()
                resource_name = 'yetanothermini'
                fields = ['title', 'abcd', 'mnop']
                include_absolute_url = True

        yetanother = YetAnotherMiniResource()
        self.assertEqual(len(yetanother.fields), 5)
        self.assertEqual(sorted(yetanother.fields.keys()), ['abcd', 'absolute_url', 'mnop', 'resource_uri', 'title'])
        self.assertEqual(len(yetanother._meta.queryset.all()), 6)
        self.assertEqual(yetanother._meta.resource_name, 'yetanothermini')

    def test_nullable_toone_full_hydrate(self):
        nrrnr = NullableRelatedNoteResource()

        # Regression: not specifying the ToOneField should still work if
        # it is nullable.
        bundle_1 = Bundle(data={
            'subjects': [],
        })

        hydrated1 = nrrnr.full_hydrate(bundle_1)

        self.assertEqual(hydrated1.data.get('author'), None)
        self.assertEqual(hydrated1.data['subjects'], [])

    def test_optional_required_data(self):
        # Regression: You have a FK field that's required on the model
        # but you want to optionally allow the user to omit it and use
        # custom ``hydrate_*`` method to populate it if it's not
        # present.
        nmbr = NullableMediaBitResource()

        bundle_1 = Bundle(data={
            'title': "Foo",
        })

        if django.VERSION >= (1, 10):
            hydrated1 = nmbr.full_hydrate(bundle_1)
            self.assertEqual(hydrated1.obj.title, "Foo")
            try:
                self.assertEqual(hydrated1.obj.note, None)
            except ObjectDoesNotExist:
                pass
        else:
            with self.assertRaises(ValueError):
                # This is where things blow up, because you can't assign
                # ``None`` to a required FK.
                hydrated1 = nmbr.full_hydrate(bundle_1)

        # So we introduced ``blank=True``.
        bmbr = BlankMediaBitResource()
        hydrated1 = bmbr.full_hydrate(bundle_1)
        self.assertEqual(hydrated1.obj.title, "Foo")
        self.assertEqual(hydrated1.obj.note.pk, 1)

    def test_nullable_tomany_full_hydrate(self):
        nrrnr = NullableRelatedNoteResource()
        bundle_1 = Bundle(data={
            'author': '/api/v1/user/1/',
            'subjects': [],
        })

        # Now load up the data.
        hydrated = nrrnr.full_hydrate(bundle_1)
        hydrated = nrrnr.hydrate_m2m(hydrated)

        self.assertEqual(hydrated.data['author'], '/api/v1/user/1/')
        self.assertEqual(hydrated.data['subjects'], [])

        # Regression: not specifying the tomany field should still work if
        # it is nullable.
        bundle_2 = Bundle(data={
            'author': '/api/v1/user/1/',
        })

        hydrated2 = nrrnr.full_hydrate(bundle_2)
        hydrated2 = nrrnr.hydrate_m2m(hydrated2)

        self.assertEqual(hydrated2.data['author'], '/api/v1/user/1/')
        self.assertEqual(hydrated2.data['subjects'], [])

        # Regression pt. II - Make sure saving the objects works.
        nrrnr.obj_create(bundle_2)
        self.assertEqual(hydrated2.obj.author.username, u'johndoe')
        self.assertEqual(hydrated2.obj.subjects.count(), 0)

    def test_per_user_authorization(self):
        from django.contrib.auth.models import AnonymousUser, User

        punr = PerUserNoteResource()
        empty_request = HttpRequest()
        empty_request.method = 'GET'
        empty_request.GET = {'format': 'json'}

        anony_request = HttpRequest()
        anony_request.method = 'GET'
        anony_request.GET = {'format': 'json'}
        anony_request.user = AnonymousUser()

        authed_request = HttpRequest()
        authed_request.method = 'GET'
        authed_request.GET = {'format': 'json'}
        authed_request.user = User.objects.get(username='johndoe')

        authed_request_2 = HttpRequest()
        authed_request_2.method = 'GET'
        authed_request_2.GET = {'format': 'json'}
        authed_request_2.user = User.objects.get(username='janedoe')

        self.assertEqual(punr._meta.queryset.count(), 6)

        # Requests without a user get all active objects, regardless of author.
        empty_bundle = punr.build_bundle(request=empty_request)
        self.assertEqual(punr.authorized_read_list(punr.get_object_list(empty_request), empty_bundle).count(), 4)
        self.assertEqual(punr._pre_limits, 0)
        # Shouldn't hit the DB yet.
        self.assertEqual(punr._post_limits, 0)
        self.assertEqual(len(json.loads(force_str(punr.get_list(request=empty_request).content))['objects']), 4)

        # Requests with an Anonymous user get no objects.
        anony_bundle = punr.build_bundle(request=anony_request)
        self.assertEqual(punr.authorized_read_list(punr.get_object_list(anony_request), anony_bundle).count(), 0)
        self.assertEqual(len(json.loads(force_str(punr.get_list(request=anony_request).content))['objects']), 0)

        # Requests with an authenticated user get all objects for that user
        # that are active.
        authed_bundle = punr.build_bundle(request=authed_request)
        self.assertEqual(punr.authorized_read_list(punr.get_object_list(authed_request), authed_bundle).count(), 2)
        self.assertEqual(len(json.loads(force_str(punr.get_list(request=authed_request).content))['objects']), 2)

        # Demonstrate that a different user gets different objects.
        authed_bundle_2 = punr.build_bundle(request=authed_request_2)
        self.assertEqual(punr.authorized_read_list(punr.get_object_list(authed_request_2), authed_bundle_2).count(), 2)
        self.assertEqual(len(json.loads(force_str(punr.get_list(request=authed_request_2).content))['objects']), 2)
        self.assertEqual(list(punr.authorized_read_list(punr.get_object_list(authed_request), authed_bundle).values_list('id', flat=True)), [1, 2])
        self.assertEqual(list(punr.authorized_read_list(punr.get_object_list(authed_request_2), authed_bundle_2).values_list('id', flat=True)), [4, 6])

    def test_per_object_authorization(self):
        ponr = PerObjectNoteResource()
        empty_request = HttpRequest()
        empty_request.method = 'GET'
        empty_request.GET = {'format': 'json'}

        self.assertEqual(ponr._meta.queryset.count(), 6)
        empty_bundle = ponr.build_bundle(request=empty_request)

        # Should return only two objects with 'post' in the ``title``.
        self.assertEqual(len(ponr.get_object_list(empty_request)), 6)
        self.assertEqual(len(ponr.authorized_read_list(ponr.get_object_list(empty_request), empty_bundle)), 2)
        self.assertEqual(ponr._pre_limits, 0)
        # Since the objects weren't filtered, we hit everything.
        self.assertEqual(ponr._post_limits, 6)

        self.assertEqual(len(json.loads(force_str(ponr.get_list(request=empty_request).content))['objects']), 2)
        self.assertEqual(ponr._pre_limits, 0)
        # Since the objects weren't filtered, we again hit everything.
        self.assertEqual(ponr._post_limits, 6)

        empty_request.GET['is_active'] = True
        self.assertEqual(len(json.loads(force_str(ponr.get_list(request=empty_request).content))['objects']), 2)
        self.assertEqual(ponr._pre_limits, 0)
        # This time, the objects were filtered, so we should only iterate over
        # a (hopefully much smaller) subset.
        self.assertEqual(ponr._post_limits, 4)

    def regression_test_per_object_detail(self):
        ponr = PerObjectNoteResource()
        empty_request = type('MockRequest', (object,), {'GET': {}})
        base_bundle = Bundle(request=empty_request)

        self.assertEqual(ponr._meta.queryset.count(), 6)

        # Regression: Make sure that simple ``get_detail`` requests work.
        self.assertTrue(isinstance(ponr.obj_get(bundle=base_bundle, pk=1), Note))
        self.assertEqual(ponr.obj_get(bundle=base_bundle, pk=1).pk, 1)
        self.assertEqual(ponr._pre_limits, 0)
        self.assertEqual(ponr._post_limits, 1)

        with self.assertRaises(MultipleObjectsReturned) as ctx:
            ponr.obj_get(bundle=base_bundle, is_active=True, pk__gte=1)
        e = ctx.exception
        self.assertEqual(str(e), "More than 'Note' matched 'is_active=True, pk__gte=1'.")

        with self.assertRaises(Note.DoesNotExist) as ctx:
            ponr.obj_get(bundle=base_bundle, pk=1000000)
        e = ctx.exception
        self.assertEqual(str(e), "Couldn't find an instance of 'Note' which matched 'pk=1000000'.")

    def test_browser_cache(self):
        resource = NoteResource()
        request = MockRequest()
        request.GET = {'format': 'json'}

        # First as a normal request.
        resp = resource.wrap_view('dispatch_detail')(request, pk=1)
        # resp = resource.get_detail(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')
        self.assertTrue(resp.has_header('Cache-Control'))
        self.assertEqual(resp['Cache-Control'], 'no-cache')

        # Now as Ajax.
        request.META = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        resp = resource.wrap_view('dispatch_detail')(request, pk=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), '{"content": "This is my very first post using my shiny new API. Pretty sweet, huh?", "created": "2010-03-30T20:05:00", "id": 1, "is_active": true, "resource_uri": "/api/v1/notes/1/", "slug": "first-post", "title": "First Post!", "updated": "2010-03-30T20:05:00"}')
        self.assertTrue(resp.has_header('cache-control'))
        self.assertEqual(resp['Cache-Control'], 'no-cache')

    def test_custom_paginator(self):
        mock_request = MockRequest()
        customs = CustomPageNoteResource().get_list(mock_request)
        data = json.loads(customs.content.decode('utf-8'))
        self.assertEqual(len(data), 3)
        self.assertEqual(len(data['objects']), 6)
        self.assertEqual(data['extra'], 'Some extra stuff here.')

    def test_readonly_full_hydrate(self):
        rornr = ReadOnlyRelatedNoteResource()
        note = Note.objects.get(pk=1)
        dbundle = Bundle(obj=note)

        # Make sure the field is there on read.
        dehydrated = rornr.full_dehydrate(dbundle)
        self.assertTrue('author' in dehydrated.data)

        # Now check that it can be omitted in ``full_hydrate``
        hbundle = Bundle(obj=note, data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0),
        })
        hydrated = rornr.full_hydrate(hbundle)
        self.assertEqual(hydrated.obj.author.username, 'johndoe')

        # It also shouldn't accept a new value & should silently ignore it.
        hbundle_2 = Bundle(obj=note, data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0),
            'author': '/api/v1/users/2/',
        })
        hydrated_2 = rornr.full_hydrate(hbundle_2)
        self.assertEqual(hydrated_2.obj.author.username, 'johndoe')

    def test_readonly_save_related(self):
        rornr = ReadOnlyRelatedNoteResource()
        note = Note.objects.get(pk=1)
        dbundle = Bundle(obj=note)

        # Make sure the field is there on read.
        dehydrated = rornr.full_dehydrate(dbundle)
        self.assertTrue('author' in dehydrated.data)

        # Fetch the bundle
        hbundle = Bundle(obj=note, data={
            'name': 'Daniel',
            'view_count': 6,
            'date_joined': aware_datetime(2010, 2, 15, 12, 0, 0),
            'author': '/api/v1/users/2/',
        })
        hydrated = rornr.full_hydrate(hbundle)

        # Get the related object.
        related_obj = getattr(hydrated.obj, "author")

        # Monkey Patch save to raise an exception
        def fake_save(*args, **kwargs):
            raise Exception("save() called in a readonly field")

        _real_save = related_obj.save

        try:
            related_obj.save = fake_save

            rornr.save_related(hydrated)
        finally:
            related_obj.save = _real_save

    def test_collection_name(self):
        resource = AlternativeCollectionNameNoteResource()
        request = HttpRequest()
        response = resource.get_list(request)
        response_data = json.loads(force_str(response.content))
        self.assertTrue('alt_objects' in response_data)

    def test_collection_name_patch_list(self):
        """Test that patch list accepts alternative names"""
        resource = AlternativeCollectionNameNoteResource()
        request = HttpRequest()
        request._body = request._raw_post_data = json.dumps({
            'alt_objects_delete': [],
            'alt_objects': [{'title': 'Testing'}]
        })
        request._read_started = False

        response = resource.patch_list(request)
        self.assertEqual(response.status_code, 202)


class BasicAuthResourceTestCase(TestCase):
    fixtures = ['note_testdata.json']

    def test_dispatch_list(self):
        resource = BasicAuthNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resp = resource.dispatch_list(request)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 401)

        # Try again with ``wrap_view`` for sanity.
        resp = resource.wrap_view('dispatch_list')(request)
        self.assertEqual(resp.status_code, 401)

        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass'.encode('utf-8')).decode('utf-8')

        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)

    def test_dispatch_detail(self):
        resource = BasicAuthNoteResource()
        request = HttpRequest()
        request.GET = {'format': 'json'}
        request.method = 'GET'

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            resource.dispatch_detail(request, pk=1)
        e = ctx.exception
        self.assertEqual(e.response.status_code, 401)

        # Try again with ``wrap_view`` for sanity.
        resp = resource.wrap_view('dispatch_detail')(request, pk=1)
        self.assertEqual(resp.status_code, 401)

        john_doe = User.objects.get(username='johndoe')
        john_doe.set_password('pass')
        john_doe.save()
        request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % base64.b64encode('johndoe:pass'.encode('utf-8')).decode('utf-8')

        resp = resource.dispatch_list(request)
        self.assertEqual(resp.status_code, 200)


# Test out the 500 behavior.
class YouFail(Exception):
    pass


class YouFailWithResponseAttr(Exception):
    response = None


class BustedResource(BasicResource):
    err_class = YouFail

    def get_list(self, request, **kwargs):
        raise self.err_class("Something blew up.")

    def get_detail(self, request, **kwargs):
        raise NotFound("It's just not there.")

    def post_list(self, request, **kwargs):
        raise Http404("Not here either")

    def post_detail(self, request, **kwargs):
        raise self.err_class("<script>alert(1)</script>")


@override_settings(TASTYPIE_FULL_DEBUG=False, TASTYPIE_CANNED_ERROR="Sorry, this request could not be processed. Please try again later.")
class BustedResourceTestCase(TestCase):
    def setUp(self):
        super(BustedResourceTestCase, self).setUp()

        self.resource = BustedResource()
        self.request = HttpRequest()
        self.request.GET = {'format': 'json'}
        self.request.method = 'GET'

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=True)
    def test_debug_on_with_full(self):
        with self.assertRaises(self.resource.err_class):
            self.resource.wrap_view('get_list')(self.request, pk=1)

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=False)
    def test_debug_on_without_full(self):
        mail.outbox = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(content['error_message'], 'Something blew up.')
        self.assertTrue(len(content['traceback']) > 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEBUG=False, TASTYPIE_FULL_DEBUG=False)
    def test_debug_off(self):
        SimpleHandler.logged = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Sorry, this request could not be processed. Please try again later."}')
        self.assertEqual(len(SimpleHandler.logged), 1)

        # Ensure that 404s don't send email.
        resp = self.resource.wrap_view('get_detail')(self.request, pk=10000000)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Sorry, this request could not be processed. Please try again later."}')
        self.assertEqual(len(SimpleHandler.logged), 1)
        SimpleHandler.logged = []

    @override_settings(DEBUG=False, TASTYPIE_FULL_DEBUG=False, TASTYPIE_CANNED_ERROR="Oops, you bwoke it.")
    def test_debug_off_custom_message(self):
        SimpleHandler.logged = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Oops, you bwoke it."}')
        self.assertEqual(len(SimpleHandler.logged), 1)
        SimpleHandler.logged = []

    def test_http404_raises_404(self):
        self.request.method = 'POST'
        resp = self.resource.wrap_view('post_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 404)

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=False)
    def test_escaping(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST = {
            'whatever': 'stuff',
        }
        res = self.resource.wrap_view('dispatch_detail')(request, pk=1)
        self.assertEqual(res.status_code, 500)
        err_data = json.loads(res.content.decode('utf-8'))
        self.assertTrue('&lt;script&gt;alert(1)&lt;/script&gt;' in err_data['error_message'])


@override_settings(TASTYPIE_FULL_DEBUG=False, TASTYPIE_CANNED_ERROR="Sorry, this request could not be processed. Please try again later.")
class BustedResourceWithNoneResponseErrorAttrTestCase(TestCase):
    def setUp(self):
        super(BustedResourceWithNoneResponseErrorAttrTestCase, self).setUp()

        self.resource = BustedResource()
        self.resource.err_class = YouFailWithResponseAttr
        self.request = HttpRequest()
        self.request.GET = {'format': 'json'}
        self.request.method = 'GET'

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=True)
    def test_debug_on_with_full(self):
        with self.assertRaises(self.resource.err_class):
            self.resource.wrap_view('get_list')(self.request, pk=1)

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=False)
    def test_debug_on_without_full(self):
        mail.outbox = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(content['error_message'], 'Something blew up.')
        self.assertTrue(len(content['traceback']) > 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEBUG=False, TASTYPIE_FULL_DEBUG=False)
    def test_debug_off(self):
        SimpleHandler.logged = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Sorry, this request could not be processed. Please try again later."}')
        self.assertEqual(len(SimpleHandler.logged), 1)

        # Ensure that 404s don't send email.
        resp = self.resource.wrap_view('get_detail')(self.request, pk=10000000)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Sorry, this request could not be processed. Please try again later."}')
        self.assertEqual(len(SimpleHandler.logged), 1)
        SimpleHandler.logged = []

    @override_settings(DEBUG=False, TASTYPIE_FULL_DEBUG=False, TASTYPIE_CANNED_ERROR="Oops, you bwoke it.")
    def test_debug_off_custom_message(self):
        SimpleHandler.logged = []

        resp = self.resource.wrap_view('get_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode('utf-8'), '{"error_message": "Oops, you bwoke it."}')
        self.assertEqual(len(SimpleHandler.logged), 1)
        SimpleHandler.logged = []

    def test_http404_raises_404(self):
        self.request.method = 'POST'
        resp = self.resource.wrap_view('post_list')(self.request, pk=1)
        self.assertEqual(resp.status_code, 404)

    @override_settings(DEBUG=True, TASTYPIE_FULL_DEBUG=False)
    def test_escaping(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST = {
            'whatever': 'stuff',
        }
        res = self.resource.wrap_view('dispatch_detail')(request, pk=1)
        self.assertEqual(res.status_code, 500)
        err_data = json.loads(res.content.decode('utf-8'))
        self.assertTrue('&lt;script&gt;alert(1)&lt;/script&gt;' in err_data['error_message'])


class ObjectlessResource(Resource):
    test = fields.CharField(default='objectless_test')

    class Meta:
        resource_name = 'objectless'


class ObjectlessResourceTestCase(TestCase):
    def test_build_bundle(self):
        resource = ObjectlessResource()

        bundle = resource.build_bundle()

        self.assertTrue(bundle is not None)


class GetResponseClassForExceptionTestCase(TestCase):
    def setUp(self):
        self.resource = Resource()
        self.resource.error_response = Mock()
        self.request = Mock()

    def test_unsupportedformat(self):
        response_class = self.resource.get_response_class_for_exception(
            self.request,
            UnsupportedFormat('A message')
        )
        self.assertEqual(response_class, http.HttpBadRequest)

    def test_unsupportedserializationformat(self):
        response_class = self.resource.get_response_class_for_exception(
            self.request,
            UnsupportedSerializationFormat('text/foo')
        )
        self.assertEqual(response_class, http.HttpNotAcceptable)

    def test_unsupporteddeserializationformat(self):
        response_class = self.resource.get_response_class_for_exception(
            self.request,
            UnsupportedDeserializationFormat('text/foo')
        )
        self.assertEqual(response_class, http.HttpUnsupportedMediaType)

    def test_unknownerror(self):
        response_class = self.resource.get_response_class_for_exception(
            self.request,
            Exception('A message')
        )
        self.assertEqual(response_class, http.HttpApplicationError)


class Handle500TestCase(TestCase):
    def setUp(self):
        self.resource = Resource()
        self.resource.error_response = Mock()
        self.request = Mock()

    @override_settings(DEBUG=True)
    @patch('tastypie.resources.traceback')
    def test_unsupported_format_debug(self, traceback):
        traceback.format_exception = Mock(return_value=[])

        msg = 'Unknown format message'
        exc = UnsupportedFormat(msg)

        self.resource._handle_500(self.request, exc)

        self.assertEqual(self.resource.error_response.call_count, 1)

        args, kwargs = self.resource.error_response.call_args
        self.assertEqual(args[1]['error_message'], msg)
        self.assertEqual(kwargs['response_class'], http.HttpBadRequest)

    @override_settings(DEBUG=True)
    @patch('tastypie.resources.traceback')
    def test_unsupportedserializationformat_debug(self, traceback):
        traceback.format_exception = Mock(return_value=[])

        format = 'text/foo'
        exc = UnsupportedSerializationFormat(format)

        self.resource._handle_500(self.request, exc)

        self.assertEqual(self.resource.error_response.call_count, 1)

        args, kwargs = self.resource.error_response.call_args
        self.assertEqual(
            args[1]['error_message'],
            UnsupportedSerializationFormat._msg_template % format
        )
        self.assertEqual(kwargs['response_class'], http.HttpNotAcceptable)

    @override_settings(DEBUG=True)
    @patch('tastypie.resources.traceback')
    def test_unsupporteddeserializationformat_debug(self, traceback):
        traceback.format_exception = Mock(return_value=[])

        format = 'text/foo'
        exc = UnsupportedDeserializationFormat(format)

        self.resource._handle_500(self.request, exc)

        self.assertEqual(self.resource.error_response.call_count, 1)

        args, kwargs = self.resource.error_response.call_args
        self.assertEqual(
            args[1]['error_message'],
            UnsupportedDeserializationFormat._msg_template % format
        )
        self.assertEqual(kwargs['response_class'], http.HttpUnsupportedMediaType)

    @override_settings(DEBUG=False)
    @patch('tastypie.resources.traceback')
    def test_unsupported_format_no_debug(self, traceback):
        traceback.format_exception = Mock(return_value=[])

        msg = 'Unknown format message'
        exc = UnsupportedFormat(msg)

        self.resource._handle_500(self.request, exc)

        self.assertEqual(self.resource.error_response.call_count, 1)

        args, kwargs = self.resource.error_response.call_args
        self.assertEqual(kwargs['response_class'], http.HttpBadRequest)

    @patch('tastypie.resources.sys')
    def test_unicode_exception(self, mock_sys):
        exc = None
        try:
            raise Exception(u"á! á! I'll get all the á's out of my body!")
        except Exception as e:
            exc = e
            mock_sys.exc_info.return_value = sys.exc_info()

        self.resource._handle_500(self.request, exc)

        self.assertEqual(self.resource.error_response.call_count, 1)

        args, kwargs = self.resource.error_response.call_args
        self.assertEqual(kwargs['response_class'], http.HttpApplicationError)


class ModelDeclarativeMetaclassTestCase(TestCase):
    """
    Regression tests for #1475
    """

    def test__fields_and_queryset_specified__object_class_set(self):
        class MyResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()
                fields = ['title']

        resource = MyResource()
        resource._meta.object_class = Note

    def test__queryset_but_no_fields_specified__object_class_set(self):
        class MyResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()

        resource = MyResource()
        resource._meta.object_class = Note

    def test__1475_example_resource(self):
        class MyResource(ModelResource):
            class Meta:
                queryset = Note.objects.all()
                fields = ['title']
                allowed_methods = ['get']
                resource_name = 'my_resource'
                authentication = BasicAuthentication()
                include_resource_uri = False

        resource = MyResource()
        resource._meta.object_class = Note
