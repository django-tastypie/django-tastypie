import warnings
warnings.simplefilter('ignore', Warning)

from core.tests.api import *
from core.tests.authentication import *
from core.tests.authorization import *
from core.tests.cache import *
from core.tests.commands import *
from core.tests.fields import *
from core.tests.http import *
from core.tests.paginator import *
from core.tests.resources import *
from core.tests.serializers import *
from core.tests.throttle import *
from core.tests.utils import *
from core.tests.validation import *
