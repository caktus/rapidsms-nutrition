from __future__ import unicode_literals
from decimal import Decimal

from django import forms

from rapidsms.conf import settings

from healthcare.api import client
from healthcare.exceptions import PatientDoesNotExist, ProviderDoesNotExist

from nutrition.models import Report
from nutrition.fields import NullDecimalField, NullYesNoField, PlainErrorList


class NutritionFormBase(object):

    def __init__(self, *args, **kwargs):
        # The connection is used to retrieve the reporter.
        self.connection = kwargs.pop('connection')
        super(NutritionFormBase, self).__init__(*args, **kwargs)

    def clean(self):
        self.clean_connection()  # Do this before attempting further cleaning.
        return super(NutritionFormBase, self).clean()

    def clean_connection(self):
        """Validate that the reporter is registered and active."""
        pass  # TODO

    def clean_patient_id(self):
        """Validate that the patient is registered and active."""
        patient_id = self.cleaned_data['patient_id']
        source = settings.NUTRITION_PATIENT_HEALTHCARE_SOURCE
        try:
            patient = client.patients.get(patient_id, source=source)
        except PatientDoesNotExist:
            msg = self.fields['patient_id'].error_messages['invalid']
            raise forms.ValidationError(msg)
        if patient['status'] != 'A':
            msg = self.fields['patient_id'].error_messages['invalid']
            raise forms.ValidationError(msg)
        self.patient = patient
        return patient_id

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


class CreateReportForm(NutritionFormBase, forms.ModelForm):
    """
    Report form which can validate input from an SMS message. To send a null
    or unknown value, send 'x' in its place.
    """
    oedema = NullYesNoField(required=False)
    weight = NullDecimalField(min_value=Decimal('0'), max_digits=4,
            required=False)
    height = NullDecimalField(min_value=Decimal('0'), max_digits=4,
            required=False)
    muac = NullDecimalField(min_value=Decimal('0'), max_digits=4,
            required=False)

    class Meta:
        model = Report
        fields = ('patient_id', 'weight', 'height', 'muac', 'oedema')

    def __init__(self, *args, **kwargs):
        # Descriptive field error messages.
        self.messages = {
            'patient_id': 'Nutrition reports must be for a patient who '\
                    'is registered and active.',
            'weight': 'Please send a positive value (in kg) for weight.',
            'height': 'Please send a positive value (in cm) for height.',
            'muac': 'Please send a positive value (in cm) for mid-upper '\
                    'arm circumference.',
            'oedema': 'Please send Y or N to indicate whether the patient '\
                    'has oedema.',
        }
        self.messages.update(kwargs.pop('messages', {}))

        if 'error_class' not in kwargs:
            kwargs['error_class'] = PlainErrorList

        super(CreateReportForm, self).__init__(*args, **kwargs)

        # Set the error messages.
        for field_name in self.messages:
            for msg_type in self.fields[field_name].error_messages:
                field = self.fields[field_name]
                field.error_messages[msg_type] = self.messages[field_name]

        # Add more specific sizing messages.
        for field_name in ('weight', 'height', 'muac'):
            field = self.fields[field_name]
            field.error_messages['max_digits'] = 'Nutrition report '\
                    'measurements should be no more than %s digits in length.'

    def save(self, *args, **kwargs):
        self.instance.global_patient_id = self.patient['id']
        return super(CreateReportForm, self).save(*args, **kwargs)
