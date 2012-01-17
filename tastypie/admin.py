from django.conf import settings
from django.contrib import admin


if 'django.contrib.auth' in settings.INSTALLED_APPS:
    from django.contrib.auth.models import User
    from tastypie.models import ApiKey

    class ApiKeyInline(admin.StackedInline):
        model = ApiKey
        extra = 0

    # Gross, gross, gross.
    # Also, depends on the ordering of ``INSTALLED_APPS``.
    m_admin = admin.site._registry[User]
    m_admin.inlines.append(ApiKeyInline)

    # Django 1.3 & below.
    if hasattr(m_admin, 'inline_instances'):
        m_admin.inline_instances.append(ApiKeyInline(User, admin.site))

    # Also.
    admin.site.register(ApiKey)
