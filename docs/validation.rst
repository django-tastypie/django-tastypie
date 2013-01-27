.. _ref-validation:

==========
Validation
==========

Validation allows you to ensure that the data being submitted by the user
is appropriate for storage. This can range from simple type checking on up
to complex validation that compares different fields together.

If the data is valid, an empty dictionary is returned and processing continues
as normal. If the data is invalid, a dictionary of error messages (keys being
the field names, values being a list of error messages) is immediately 
returned to the user, serialized in the format they requested.

Usage
=====

Using these classes is simple. Simply provide them (or your own class) as a
``Meta`` option to the ``Resource`` in question. For example::

    from django.contrib.auth.models import User
    from tastypie.validation import Validation
    from tastypie.resources import ModelResource


    class UserResource(ModelResource):
        class Meta:
            queryset = User.objects.all()
            resource_name = 'auth/user'
            excludes = ['email', 'password', 'is_superuser']
            # Add it here.
            validation = Validation()


Validation Options
==================

Tastypie ships with the following ``Validation`` classes:

``Validation``
~~~~~~~~~~~~~~

The no-op validation option, the data submitted is always considered to be
valid.

This is the default class hooked up to ``Resource/ModelResource``.

``FormValidation``
~~~~~~~~~~~~~~~~~~

A more complex form of validation, this class accepts a ``form_class`` argument
to its constructor. You supply a Django ``Form`` (or ``ModelForm``, though
``save`` will never get called) and Tastypie will verify the ``data`` in the
``Bundle`` against the form.

This class **DOES NOT** alter the data sent, only verifies it. If you
want to alter the data, please use the ``CleanDataFormValidation`` class
instead.

.. warning::

    Data in the bundle must line up with the fieldnames in the ``Form``. If they
    do not, you'll need to either munge the data or change your form.

Usage looks like::

    from django import forms

    class NoteForm(forms.Form):
        title = forms.CharField(max_length=100)
        slug = forms.CharField(max_length=50)
        content = forms.CharField(required=False, widget=forms.Textarea)
        is_active = forms.BooleanField()

    form = FormValidation(form_class=NoteForm)

``CleanedDataFormValidation``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to the ``FormValidation`` class, this uses a Django ``Form`` to handle
validation. **However**, it will use the ``form.cleaned_data`` to replace the
``bundle`` data sent by user! Usage is identical to ``FormValidation``.


Implementing Your Own Validation
================================

Implementing your own ``Validation`` classes is a simple process. The
constructor can take whatever ``**kwargs`` it needs (if any). The only other
method to implement is the ``is_valid`` method::

    from tastypie.validation import Validation


    class AwesomeValidation(Validation):
        def is_valid(self, bundle, request=None):
            if not bundle.data:
                return {'__all__': 'Not quite what I had in mind.'}

            errors = {}

            for key, value in bundle.data.items():
                if not isinstance(value, basestring):
                    continue

                if not 'awesome' in value:
                    errors[key] = ['NOT ENOUGH AWESOME. NEEDS MORE.']

            return errors

Under this validation, every field that's a string is checked for the word
'awesome'. If it's not in the string, it's an error.
