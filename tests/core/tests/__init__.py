import doctest
import warnings
warnings.simplefilter('ignore', Warning)  # noqa

from core.tests.api import *  # noqa
from core.tests.authentication import *  # noqa
from core.tests.authorization import *  # noqa
from core.tests.cache import *  # noqa
from core.tests.commands import *  # noqa
from core.tests.fields import *  # noqa
from core.tests.http import *  # noqa
from core.tests.paginator import *  # noqa
from core.tests.resources import *  # noqa
from core.tests.serializers import *  # noqa
from core.tests.throttle import *  # noqa
from core.tests.utils import *  # noqa
from core.tests.validation import *  # noqa


# Explicitly add doctests to suite; Django's test runner stopped
# running them automatically around version 1.6
def load_tests(loader, tests, ignore):
    from tastypie.utils import validate_jsonp
    tests.addTests(doctest.DocTestSuite(validate_jsonp))
    return tests
