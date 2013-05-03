from __future__ import print_function
from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from tastypie.compat import User
from tastypie.models import ApiKey


class Command(NoArgsCommand):
    help = "Goes through all users and adds API keys for any that don't have one."

    def handle_noargs(self, **options):
        """Goes through all users and adds API keys for any that don't have one."""
        self.verbosity = int(options.get('verbosity', 1))

        for user in User.objects.all().iterator():
            try:
                api_key = ApiKey.objects.get(user=user)

                if not api_key.key:
                    # Autogenerate the key.
                    api_key.save()

                    if self.verbosity >= 1:
                        print(u"Generated a new key for '%s'" % user.username)
            except ApiKey.DoesNotExist:
                api_key = ApiKey.objects.create(user=user)

                if self.verbosity >= 1:
                    print(u"Created a new key for '%s'" % user.username)
