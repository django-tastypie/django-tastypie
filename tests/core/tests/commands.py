from django.core.management import call_command
from django.db import models
from django.test import TestCase

from tastypie.compat import get_user_model
from tastypie.models import ApiKey, create_api_key


class BackfillApiKeysTestCase(TestCase):
    def setUp(self):
        super(BackfillApiKeysTestCase, self).setUp()
        self.User = get_user_model()

        # Disconnect the signal to prevent automatic key generation.
        models.signals.post_save.disconnect(create_api_key, sender=self.User)

    def tearDown(self):
        # Reconnect the signal.
        models.signals.post_save.connect(create_api_key, sender=self.User)
        super(BackfillApiKeysTestCase, self).tearDown()

    def test_command(self):
        self.assertEqual(ApiKey.objects.count(), 0)

        # Create a new User that ought not to have an API key.
        new_user = self.User.objects.create_user(username='mr_pants', password='password', email='mister@pants.com')

        self.assertEqual(ApiKey.objects.count(), 0)

        call_command('backfill_api_keys', verbosity=0)

        self.assertEqual(ApiKey.objects.count(), 1)

        self.assertEqual(ApiKey.objects.filter(user=new_user).count(), 1)
