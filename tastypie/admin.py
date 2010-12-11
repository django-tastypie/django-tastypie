from django.contrib import admin

if 'django.contrib.auth' in settings.INSTALLED_APPS:
    from tastypie.models import ApiKey

    class ApiKeyInline(admin.StackedInline):
        model = ApiKey
        extra = 0

