from django.core.serializers import json
from django.utils import simplejson
from django.utils.encoding import force_unicode
from piecrust.serializers import Serializer as PiecrustSerializer
from piecrust.serializers import simplejson


class Serializer(PiecrustSerializer):
    """
    A swappable class for serialization.

    This handles most types of data as well as the following output formats::

        * json
        * jsonp
        * xml
        * yaml
        * html
        * plist (see http://explorapp.com/biplist/)

    It was designed to make changing behavior easy, either by overridding the
    various format methods (i.e. ``to_json``), by changing the
    ``formats/content_types`` options or by altering the other hook methods.
    """
    def force_unicode(self, thing):
        return force_unicode(thing)

    def to_json(self, data, options=None):
        """
        Given some Python data, produces JSON output.
        """
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)
