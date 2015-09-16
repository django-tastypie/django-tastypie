import json

from django.test import TestCase


class CustomUserTestCase(TestCase):

    def test_datefield_return_correct_error_message(self):
        """
        When a invalid date is provided, return the right message in the
        response object.
        """
        data = {
            "password": "sha1$6efc0$f92efe9fd8542f25a7be94871ea45aa95de57161",
            "email": "tester@example.com",
            "is_active": True,
            "is_admin": False,
            "date_of_birth": "1976-17-08"  # Format for valid date: YYYY-MM-DD
        }
        response = self.client.post('/api/v2/customusers/',
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        err = "'1976-17-08' value has the correct format (YYYY-MM-DD) but it" \
              + " is an invalid date."
        self.assertIn(err, response.content)
