from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import models
from django.test import TestCase
from tastypie.models import ApiKey, create_api_key


class BackfillApiKeysTestCase(TestCase):
    def setUp(self):
        super(BackfillApiKeysTestCase, self).setUp()
        
        # Disconnect the signal to prevent automatic key generation.
        models.signals.post_save.disconnect(create_api_key, sender=User)
    
    def tearDown(self):
        # Reconnect the signal.
        models.signals.post_save.connect(create_api_key, sender=User)
        super(BackfillApiKeysTestCase, self).tearDown()
    
    def test_command(self):
        self.assertEqual(ApiKey.objects.count(), 0)
        
        # Create a new User that ought not to have an API key.
        new_user = User.objects.create_user(username='mr_pants', password='password', email='mister@pants.com')
        
        self.assertEqual(ApiKey.objects.count(), 0)
        
        try:
            ApiKey.objects.get(user=new_user)
            self.fail('Wha? The user mysteriously has a key? WTF?')
        except ApiKey.DoesNotExist:
            pass
        
        call_command('backfill_api_keys', verbosity=0)
        self.assertEqual(ApiKey.objects.count(), 1)
        
        try:
            api_key = ApiKey.objects.get(user=new_user)
        except ApiKey.DoesNotExist:
            self.fail("No key means the command didn't work.")
