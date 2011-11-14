from django.http import HttpRequest


# In a separate file to avoid circular imports...
class Bundle(object):
    """
    A small container for instances and converted data for the
    ``dehydrate/hydrate`` cycle.

    Necessary because the ``dehydrate/hydrate`` cycle needs to access data at
    different points.
    """
    def __init__(self, obj=None, data=None, request=None, related_obj=None, related_name=None):
        self.obj = obj
        self.data = data or {}
        self.request = request or HttpRequest()
        self.related_obj = related_obj
        self.related_name = related_name

    def __repr__(self):
        return "<Bundle for obj: '%s' and with data: '%s'>" % (self.obj, self.data)
