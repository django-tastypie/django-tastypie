from django.test import TransactionTestCase
from django.http import HttpResponseBadRequest, HttpRequest, HttpResponse
from tastypie.middleware import TransactionMiddleware
from django.db import transaction

class TransactionMiddlewareTestCase(TransactionTestCase):
  def setUp(self):
    super(TransactionMiddlewareTestCase, self).setUp()
    transaction.enter_transaction_management()
    self.middleware = TransactionMiddleware()
    self.request = HttpRequest()

  def test_does_not_fail(self):
    response = HttpResponse()
    self.assertEquals(response, self.middleware.process_response(self.request, response))
    self.assertFalse(transaction.is_managed(), msg="Still managed")

  def test_rolled_back_on_gt_than_400(self):
    response = HttpResponseBadRequest()
    self.assertEquals(response, self.middleware.process_response(self.request, response))
    self.assertFalse(transaction.is_dirty(), msg="Rollback failed")
    self.assertFalse(transaction.is_managed(), msg="Still managed")
