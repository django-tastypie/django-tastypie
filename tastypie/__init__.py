import inspect
from tastypie.exceptions import URLReverseError


__author__ = 'Daniel Lindsley, Cody Soyland, Matt Croydon'
__version__ = (0, 4, 0)


# This is a global place where ``Api`` instances register themselves.
# Kinda sucks, but necessary with the current architecture to do url
# resolution at the ``Representation`` level.
# I don't feel totally bad about this, because the admin does similar things
# for ``formfield_overrides``, but would welcome a better idea.
# 
# Structure (when built) should look like::
#     available_apis = {
#         'v1': {
#             'class': <Api object>,
#             'resources': [
#                 'notes',
#             ],
#             'representations': {
#                 # Note - ``NoteRepresentation.__name__``, NOT ``NoteRepresentation`` the class.
#                 'NoteRepresentation': 'notes',
#             }
#         },
#         'v2': {
#             'class': <Api object>,
#             'resources': [
#                 'notes',
#                 'users',
#             ],
#             'representations': {
#                 # Note - ``CustomNoteRepresentation.__name__``, NOT ``CustomNoteRepresentation`` the class.
#                 'CustomNoteRepresentation': 'notes',
#                 'UserRepresentation': 'users',
#             }
#         },
#     }
available_apis = {}


def _add_resource(api, resource, canonical=True):
    if not api.api_name in available_apis:
        available_apis[api.api_name] = {
            'class': api,
            'resources': [],
            'representations': {},
        }
    
    if not resource.resource_name in available_apis[api.api_name]['resources']:
        available_apis[api.api_name]['resources'].append(resource.resource_name)
    
    if canonical is True:
        repr_name = resource.detail_representation.__name__
        available_apis[api.api_name]['representations'][repr_name] = resource.resource_name


def _remove_resource(api, resource):
    if not api.api_name in available_apis:
        return False
    
    try:
        resource_offset = available_apis[api.api_name]['resources'].index(resource.resource_name)
        del(available_apis[api.api_name]['resources'][resource_offset])
    except (ValueError, IndexError):
        return False
    
    if inspect.isclass(resource.detail_representation):
        representation_name = resource.detail_representation.__name__
    else:
        representation_name = resource.detail_representation.__class__.__name__
    
    if representation_name in available_apis[api.api_name]['representations']:
        if available_apis[api.api_name]['representations'][representation_name] == resource.resource_name:
            del(available_apis[api.api_name]['representations'][representation_name])
    
    return True


def _get_canonical_resource_name(api_name, representation):
    if inspect.isclass(representation) and getattr(representation, '__name__', None):
        representation_name = representation.__name__
    else:
        representation_name = representation.__class__.__name__
    
    if not api_name in available_apis:
        raise URLReverseError("The api_name '%s' does not appear to have been instantiated." % api_name)
    
    if not 'representations' in available_apis[api_name]:
        raise URLReverseError("The api_name '%s' does not appear to have any representations registered." % api_name)
    
    if not 'resources' in available_apis[api_name]:
        raise URLReverseError("The api_name '%s' does not appear to have any resources registered." % api_name)
    
    if not representation_name in available_apis[api_name]['representations']:
        raise URLReverseError("The api '%s' does not have a '%s' representation registered." % (api_name, representation_name))
    
    desired_resource_name = available_apis[api_name]['representations'][representation_name]
    
    # Now verify the resource is in the list.
    if not desired_resource_name in available_apis[api_name]['resources']:
        raise URLReverseError("The api '%s' does not have a canonical resource named '%s' registered." % (api_name, desired_resource_name))
    
    return desired_resource_name
