# In a separate file to avoid circular imports...
class Bundle(object):
    """
    A small container for instances and converted data for the
    ``dehydrate/hydrate`` cycle.
    
    Necessary because the ``dehydrate/hydrate`` cycle needs to access data at
    different points.
    """
    def __init__(self, obj=None, data=None):
        self.obj = obj
        self.data = data or {}
    
    def __repr__(self):
        return "<Bundle for obj: '%s' and with data: '%s'>" % (self.obj, self.data)
