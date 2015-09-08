from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from django.forms import ModelForm
from django.forms.models import model_to_dict


class Validation(object):
    """
    A basic validation stub that does no validation.
    """
    def __init__(self, **kwargs):
        pass

    def is_valid(self, bundle, request=None):
        """
        Performs a check on the data within the bundle (and optionally the
        request) to ensure it is valid.

        Should return a dictionary of error messages. If the dictionary has
        zero items, the data is considered valid. If there are errors, keys
        in the dictionary should be field names and the values should be a list
        of errors, even if there is only one.
        """
        return {}


class FormValidation(Validation):
    """
    A validation class that uses a Django ``Form`` to validate the data.

    This class **DOES NOT** alter the data sent, only verifies it. If you
    want to alter the data, please use the ``CleanedDataFormValidation`` class
    instead.

    This class requires a ``form_class`` argument, which should be a Django
    ``Form`` (or ``ModelForm``, though ``save`` will never be called) class.
    This form will be used to validate the data in ``bundle.data``.
    """
    def __init__(self, **kwargs):
        if 'form_class' not in kwargs:
            raise ImproperlyConfigured(
                "You must provide a 'form_class' to 'FormValidation' classes.")

        self.form_class = kwargs.pop('form_class')
        super(FormValidation, self).__init__(**kwargs)

    def form_args(self, bundle):
        data = bundle.data

        # Ensure we get a bound Form, regardless of the state of the bundle.
        if data is None:
            data = {}

        kwargs = {'data': {}}

        if hasattr(bundle.obj, 'pk'):
            if issubclass(self.form_class, ModelForm):
                kwargs['instance'] = bundle.obj

            kwargs['data'] = model_to_dict(bundle.obj)

        kwargs['data'].update(data)
        return kwargs

    def is_valid(self, bundle, request=None):
        """
        Performs a check on ``bundle.data``to ensure it is valid.

        If the form is valid, an empty list (all valid) will be returned. If
        not, a list of errors will be returned.
        """

        form = self.form_class(**self.form_args(bundle))

        if form.is_valid():
            return {}

        # The data is invalid. Let's collect all the error messages & return
        # them.
        return form.errors


class CleanedDataFormValidation(FormValidation):
    """
    A validation class that uses a Django ``Form`` to validate the data.

    This class **ALTERS** data sent by the user!!!

    This class requires a ``form_class`` argument, which should be a Django
    ``Form`` (or ``ModelForm``, though ``save`` will never be called) class.
    This form will be used to validate the data in ``bundle.data``.
    """
    def is_valid(self, bundle, request=None):
        """
        Checks ``bundle.data``to ensure it is valid & replaces it with the
        cleaned results.

        If the form is valid, an empty list (all valid) will be returned. If
        not, a list of errors will be returned.
        """
        form = self.form_class(**self.form_args(bundle))

        if form.is_valid():
            # We're different here & relying on having a reference to the same
            # bundle the rest of the process is using.
            bundle.data = form.cleaned_data
            return {}

        # The data is invalid. Let's collect all the error messages & return
        # them.
        return form.errors
