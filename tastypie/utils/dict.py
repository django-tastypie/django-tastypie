def dict_strip_unicode_keys(uni_dict):
    """
    Converts a dict of unicode keys into a dict of ascii keys.
    
    Useful for converting a dict to a kwarg-able format.
    """
    data = {}
    
    for key, value in uni_dict.items():
        data[str(key)] = value
    
    return data
