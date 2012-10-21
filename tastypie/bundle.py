from django.http import HttpRequest


# In a separate file to avoid circular imports...
class Bundle(object):
    """
    A small container for instances and converted data for the
    ``dehydrate/hydrate`` cycle.

    Necessary because the ``dehydrate/hydrate`` cycle needs to access data at
    different points.
    """
    def __init__(self, obj=None, data=None, request=None, related_obj=None, related_name=None, obj_is_new=False):
        self.obj = obj
        self.data = data or {}
        self.request = request or HttpRequest()
        self.related_obj = related_obj
        self.related_name = related_name
        self.errors = {}
        self.obj_is_new = obj_is_new

    def __repr__(self):
        return "<Bundle for obj: '%s' and with data: '%s'>" % (self.obj, self.data)

    # Should be called to install a blank object into this bundle with the obj_is_new flag
    # correctly indicating that the object does not yet exist in the database.
    def install_new_obj_from_class(self, cls):
        self.obj = cls()
        self.obj_is_new = True

    # Should be called to install an existing object into this bundle with the obj_is_new flag
    # correctly indicating that the object does exist in the database.
    def install_existing_obj(self, obj):
        self.obj = obj
        self.obj_is_new = False

    # Should be called to save the object and update the obj_is_new flag to indicate that the
    # object now actually exists in the database.
    def save_obj(self):
        self.obj.save()
        self.obj_is_new = False
