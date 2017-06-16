from django.core.exceptions import ImproperlyConfigured
from django import forms
from django.test import TestCase
from tastypie.bundle import Bundle
from tastypie.validation import Validation, FormValidation, CleanedDataFormValidation


class NoteForm(forms.Form):
    title = forms.CharField(max_length=100)
    slug = forms.CharField(max_length=50)
    content = forms.CharField(required=False, widget=forms.Textarea)
    is_active = forms.BooleanField()

    def clean_title(self):
        return self.cleaned_data.get('title', '').upper()

    # Define a custom clean to make sure non-field errors are making it
    # through.
    def clean(self):
        if not self.cleaned_data.get('content', ''):
            raise forms.ValidationError('Having no content makes for a very boring note.')

        return self.cleaned_data


class ValidationTestCase(TestCase):
    def test_init_no_args(self):
        try:
            Validation()
        except Exception:
            self.fail("Initialization failed when it should have succeeded.")

    def test_init_form_class_provided(self):
        try:
            Validation(form_class='foo')
        except Exception:
            self.fail("Initialization failed when it should have succeeded again.")

    def test_is_valid(self):
        valid = Validation()
        bundle = Bundle()
        self.assertEqual(valid.is_valid(bundle), {})

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': 'bar',
            'content': '',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {})


class FormValidationTestCase(TestCase):
    def test_init_no_args(self):
        self.assertRaises(ImproperlyConfigured, FormValidation)

    def test_init_form_class_provided(self):
        try:
            FormValidation(form_class=NoteForm)
        except Exception:
            self.fail("Initialization failed when it should have succeeded.")

    def test_is_valid(self):
        valid = FormValidation(form_class=NoteForm)
        bundle = Bundle()
        self.assertEqual(valid.is_valid(bundle), {
            'is_active': [u'This field is required.'],
            'slug': [u'This field is required.'],
            '__all__': [u'Having no content makes for a very boring note.'],
            'title': [u'This field is required.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': '123456789012345678901234567890123456789012345678901234567890',
            'content': '',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {
            'slug': [u'Ensure this value has at most 50 characters (it has 60).'],
            '__all__': [u'Having no content makes for a very boring note.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': 'bar',
            'content': '',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {
            '__all__': [u'Having no content makes for a very boring note.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': 'bar',
            'content': 'This! Is! CONTENT!',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {})
        # NOTE: Bundle data is left untouched!
        self.assertEqual(bundle.data['title'], 'Foo.')


class CleanedDataFormValidationTestCase(TestCase):
    def test_init_no_args(self):
        self.assertRaises(ImproperlyConfigured, CleanedDataFormValidation)

    def test_init_form_class_provided(self):
        try:
            CleanedDataFormValidation(form_class=NoteForm)
        except Exception:
            self.fail("Initialization failed when it should have succeeded.")

    def test_is_valid(self):
        valid = CleanedDataFormValidation(form_class=NoteForm)
        bundle = Bundle()
        self.assertEqual(valid.is_valid(bundle), {
            'is_active': [u'This field is required.'],
            'slug': [u'This field is required.'],
            '__all__': [u'Having no content makes for a very boring note.'],
            'title': [u'This field is required.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': '123456789012345678901234567890123456789012345678901234567890',
            'content': '',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {
            'slug': [u'Ensure this value has at most 50 characters (it has 60).'],
            '__all__': [u'Having no content makes for a very boring note.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': 'bar',
            'content': '',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {
            '__all__': [u'Having no content makes for a very boring note.'],
        })

        bundle = Bundle(data={
            'title': 'Foo.',
            'slug': 'bar',
            'content': 'This! Is! CONTENT!',
            'is_active': True,
        })
        self.assertEqual(valid.is_valid(bundle), {})
        # NOTE: Bundle data is modified!
        self.assertEqual(bundle.data['title'], u'FOO.')
