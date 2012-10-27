def get_user_model():
    """
    Returns active user model.

    This method is needed for loading custom User models introduced in
    Django 1.5 and backwards compatibility with earlier Django installations.
    """
    try:
        from django.contrib.auth import get_user_model
        return get_user_model()
    except ImportError:
        from django.contrib.auth.models import User
        return User
