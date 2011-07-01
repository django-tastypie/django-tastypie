from django.conf import settings
from django.contrib import admin


if 'django.contrib.auth' in settings.INSTALLED_APPS:
    from tastypie.models import ApiKey
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.models import User
    
    class ApiKeyInline(admin.StackedInline):
        model = ApiKey
        extra = 0

    class UserAdmin(UserAdmin):
        inlines = [ApiKeyInline,]

    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)

