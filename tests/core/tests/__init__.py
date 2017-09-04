import warnings
warnings.simplefilter('ignore', Warning)
import doctest

from core.tests.api import *  # flake8: noqa
from core.tests.authentication import *  # flake8: noqa
from core.tests.authorization import *  # flake8: noqa
from core.tests.cache import *  # flake8: noqa
from core.tests.commands import *  # flake8: noqa
from core.tests.fields import *  # flake8: noqa
from core.tests.http import *  # flake8: noqa
from core.tests.paginator import *  # flake8: noqa
from core.tests.resources import *  # flake8: noqa
from core.tests.serializers import *  # flake8: noqa
from core.tests.throttle import *  # flake8: noqa
from core.tests.utils import *  # flake8: noqa
from core.tests.validation import *  # flake8: noqa


# Explicitly add doctests to suite; Django's test runner stopped
# running them automatically around version 1.6
def load_tests(loader, tests, ignore):
    from tastypie.utils import validate_jsonp
    tests.addTests(doctest.DocTestSuite(validate_jsonp))
    return tests
