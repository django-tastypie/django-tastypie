from django.conf import settings
from piecrust.paginator import Paginator as PiecrustPaginator


class Paginator(PiecrustPaginator):
    """
    Limits result sets down to sane amounts for passing to the client.

    This is used in place of Django's ``Paginator`` due to the way pagination
    works. ``limit`` & ``offset`` (tastypie) are used in place of ``page``
    (Django) so none of the page-related calculations are necessary.

    This implementation also provides additional details like the
    ``total_count`` of resources seen and convenience links to the
    ``previous``/``next`` pages of data as available.

    This is implemented solely for backward-compatibility on the ``limit``
    setting.
    """
    limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)
