from django.db import transaction
from django.middleware.transaction import TransactionMiddleware

class TransactionMiddleware(TransactionMiddleware):
    """
    An extension of Djangos TransactionMiddleware, by also catching status codes
    that are over 400. If a status code over 400 occurs it will roll back the transaction.
    """

    def process_response(self, request, response):
        """Commits and leaves transaction management."""
        if response.status_code >= 400:
            self.process_exception(request, None)
            return response
        return super(TransactionMiddleware, self).process_response(request, response)
