from __future__ import unicode_literals
from decimal import Decimal

from django import forms
from django.utils.encoding import force_unicode

from healthcare.api import client
from healthcare.exceptions import PatientDoesNotExist, ProviderDoesNotExist

from nutrition.models import Report, HEALTHCARE_SOURCE
from nutrition.fields import NullDecimalField, NullYesNoField


class PlainErrorList(forms.util.ErrorList):
    """Custom error list with simple text rendering for SMS."""

    def as_text(self):
        if not self:
            return ''
        return ' '.join(['%s' % force_unicode(e) for e in self])


class CreateReportForm(forms.ModelForm):
    """
    Report form which can validate input from an SMS message. To send a null
    or unknown value, send 'x' in its place.
    """
    oedema = NullYesNoField(required=False)
    weight = NullDecimalField(min_value=Decimal('0'), required=False)
    height = NullDecimalField(min_value=Decimal('0'), required=False)
    muac = NullDecimalField(min_value=Decimal('0'), required=False)

    class Meta:
        model = Report
        fields = ('patient_id', 'weight', 'height', 'muac', 'oedema')

    def __init__(self, *args, **kwargs):
        # The connection is used to retrieve the reporting health worker.
        self.connection = kwargs.pop('connection')

        # Descriptive field error messages.
        self.messages = {
            'patient_id': 'Nutrition reports must be for a patient who is '\
                    'registered and active.',
            'weight': 'Please send a positive decimal (in kg) for weight.',
            'height': 'Please send a positive decimal (in cm) for height.',
            'muac': 'Please send a positive decimal (in cm) for mid-upper '\
                    'arm circumference.',
            'oedema': 'Please send Y or N to indicate whether the patient '\
                    'has oedema.',
        }
        self.messages.update(kwargs.pop('messages', {}))

        if 'error_class' not in kwargs:
            kwargs['error_class'] = PlainErrorList
        super(CreateReportForm, self).__init__(*args, **kwargs)

        for field_name in self.messages:
            for msg_type in self.fields[field].error_messages:
                field = self.fields[field_name]
                field.error_messages[msg_type] = self.messages[field_name]

    def clean_patient_id(self):
        """Check that patient is registered and active."""
        val = self.cleaned_data['patient_id']
        try:
            patient = client.patients.get(val, source=HEALTHCARE_SOURCE)
        except PatientDoesNotExist:
            msg = self.fields['patient_id'].error_messages['invalid']
            raise forms.ValidationError(msg)
        if patient['status'] != 'A':
            msg = self.fields['patient_id'].error_messages['invalid']
            raise forms.ValidationError(msg)
        return val

    def clean(self):
        """Check that healthcare worker is registered and active."""
        cleaned_data = super(CreateReportForm, self).clean()
        self.healthworker_id = 'placeholder'
        # TODO - Validate that connection is a registered and active
        # healthworker.
        return cleaned_data

    @property
    def error(self):
        """Condense form errors into a single error message."""
        for field in self.fields:
            # Return the first field error based on field order.
            if field in self.errors:
                return self.errors[field].as_text()
        if forms.forms.NON_FIELD_ERRORS in self.errors:
            return self.errors[NON_FIELD_ERRORS].as_text()
        return None

    def save(self, commit=True):
        self.instance.healthworker_id = self.healthworker_id
        return super(CreateReportForm, self).save(commit=commit)

