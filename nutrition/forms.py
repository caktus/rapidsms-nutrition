from __future__ import unicode_literals
from decimal import Decimal

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from healthcare.api import client
from healthcare.exceptions import PatientDoesNotExist, ProviderDoesNotExist

from nutrition.models import Report
from nutrition.fields import NullDecimalField, NullYesNoField, PlainErrorList


class NutritionFormBase(object):

    def __init__(self, *args, **kwargs):
        self.connection = kwargs.pop('connection', None)
        self.raw_text = kwargs.pop('raw_text', None)

        if 'error_class' not in kwargs:
            kwargs['error_class'] = PlainErrorList

        super(NutritionFormBase, self).__init__(*args, **kwargs)

    def _update_field_messages(self, messages):
        for field_name in messages:
            for msg_type in self.fields[field_name].error_messages:
                field = self.fields[field_name]
                field.error_messages[msg_type] = messages[field_name]

    def clean(self):
        self.clean_connection()  # Do this before attempting further cleaning.
        return super(NutritionFormBase, self).clean()

    def clean_connection(self):
        """Validate that the reporter is registered and active."""
        if self.connection:
            contact = self.connection.contact
            if not contact:
                raise forms.ValidationError(self.messages.get('connection', ''))
            try:
                reporter = client.providers.get_by_contact(contact)
            except ProviderDoesNotExist:
                raise forms.ValidationError(self.messages.get('connection', ''))
            if reporter['status'] != 'A':
                raise forms.ValidationError(self.messages.get('connection', ''))
            self.reporter = reporter
            return self.connection

    def clean_patient_id(self):
        """Validate that the patient is registered and active."""
        patient_id = self.cleaned_data['patient_id']
        source = getattr(settings, 'NUTRITION_PATIENT_HEALTHCARE_SOURCE', None)
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
            return self.errors[forms.forms.NON_FIELD_ERRORS].as_text()
        return None


class CancelReportForm(NutritionFormBase, forms.Form):
    """Cancels a patient's most recently created report."""
    patient_id = forms.CharField()

    def __init__(self, *args, **kwargs):
        # Descriptive error messages for form fields.
        field_messages = {
            'patient_id': _('Nutrition reports must be for a patient who is '
                    'registered and active.'),
        }
        field_messages.update(kwargs.pop('field_messages', {}))

        # Descriptive error messages for specific non-field errors.
        self.messages = {
            'connection': 'You are not registered as a nutrition reporter.',
        }

        super(CancelReportForm, self).__init__(*args, **kwargs)

        # Set custom field messages.
        self._update_field_messages(field_messages)

    def cancel(self):
        """Cancels the patient's most recent report. If self.connection is
        given, then the reports are filtered to only those made by connections
        of the Contact associated with self.connection.

        Raises Report.DoesNotExist if the patient has no reports.
        """
        # We do not filter on report status. It is possible that the most
        # recent report is already cancelled, but that's okay for now because
        # this feature is not intended to allow reporters to cancel all
        # reports to the beginning of time.
        filters = {'patient_id': self.cleaned_data['patient_id']}
        if self.connection:
            cxns = self.connection.contact.connection_set.all()
            filters['reporter_connection__in'] = cxns
        # Report.DoesNotExist should be handled by the caller.
        report = Report.objects.filter(**filters).latest('created_date')
        report.cancel()
        return report


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
        # Descriptive error messages for form fields.
        field_messages = {
            'patient_id': _('Nutrition reports must be for a patient who '
                    'is registered and active.'),
            'weight': _('Please send a positive value (in kg) for weight.'),
            'height': _('Please send a positive value (in cm) for height.'),
            'muac': _('Please send a positive value (in cm) for mid-upper '
                    'arm circumference.'),
            'oedema': _('Please send Y or N to indicate whether the patient '
                    'has oedema.'),
        }
        field_messages.update(kwargs.pop('field_messages', {}))

        # Descriptive error messages for specific non-field errors.
        self.messages = {
            'connection': 'You are not registered as a nutrition reporter.',
        }

        super(CreateReportForm, self).__init__(*args, **kwargs)

        # Set custom field messages.
        self._update_field_messages(field_messages)

        # Add more specific sizing messages.
        for field_name in ('weight', 'height', 'muac'):
            field = self.fields[field_name]
            field.error_messages['max_digits'] = _('Nutrition report '
                    'measurements should be no more than %s digits in length.')

    def save(self, *args, **kwargs):
        self.instance.raw_text = self.raw_text
        self.instance.global_patient_id = self.patient['id']
        if self.connection:
            self.instance.reporter_connection = self.connection
        if self.reporter:
            self.instance.global_reporter_id = self.reporter['id']
        return super(CreateReportForm, self).save(*args, **kwargs)


class ReportFilterForm(forms.Form):
    patient = forms.CharField(label='Patient ID', required=False)
    reporter = forms.CharField(label='Reporter Connection', required=False)
    status = forms.ChoiceField(choices=[('', '')] + Report.STATUSES,
            required=False)

    def _get_filters(self):
        if self.is_valid():
            filters = {}
            if self.cleaned_data['patient']:
                filters['patient_id'] = self.cleaned_data['patient']
            if self.cleaned_data['reporter']:
                filters['reporter_connection__identity'] = self.cleaned_data['reporter']
            if self.cleaned_data['status']:
                filters['status'] = self.cleaned_data['status']
            return filters

    def get_items(self, ordering=None):
        filters = self._get_filters()
        if filters is not None:
            if ordering is not None:
                return Report.objects.filter(**filters).order_by(*ordering)
            return Report.objects.filter(**filters)
