from django.core.management.base import NoArgsCommand
from tastypie.models import ApiKey
from tastypie.utils import get_user_model

class Command(NoArgsCommand):
    help = "Goes through all users and adds API keys for any that don't have one."
    
    def handle_noargs(self, **options):
        """Goes through all users and adds API keys for any that don't have one."""
        self.verbosity = int(options.get('verbosity', 1))
        auth_user_model = get_user_model()
        
        for user in auth_user_model.objects.all().iterator():
            try:
                api_key = ApiKey.objects.get(user=user)
                
                if not api_key.key:
                    # Autogenerate the key.
                    api_key.save()
                    
                    if self.verbosity >= 1:
                        print u"Generated a new key for '%s'" % user.username
            except ApiKey.DoesNotExist:
                api_key = ApiKey.objects.create(user=user)
                
                if self.verbosity >= 1:
                    print u"Created a new key for '%s'" % user.username
