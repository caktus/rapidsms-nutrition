from __future__ import unicode_literals

from django import forms
from django.utils.encoding import force_unicode

from nutrition.models import Report
from nutrition.fields import NullDecimalField, NullYesNoField


class PlainErrorList(forms.util.ErrorList):
    """Custom error list with simple text rendering for SMS."""

    def as_text(self):
        if not self:
            return ''
        return ' '.join(['%s' % force_unicode(e) for e in self])


class CreateReportForm(forms.ModelForm):
    """
    Report form which can validate input from an SMS message. All fields
    must be specified. To send a null or unknown value, send 'x' in its place.
    """
    oedema = NullYesNoField()
    height = NullDecimalField(min_value=0)
    weight = NullDecimalField(min_value=0)
    muac = NullDecimalField(min_value=0)

    class Meta:
        model = Report
        fields = ('patient_id', 'height', 'weight', 'muac', 'oedema')

    def __init__(self, *args, **kwargs):
        # The connection is used to retrieve the reporting health worker.
        self.connection = kwargs.pop('connection')

        # Descriptive field error messages.
        self.messages = {
            'oedema': 'Please send Y or N to indicate whether the patient has oedema.',
            'height': 'Please send a positive decimal (in cm) for height.',
            'weight': 'Please send a positive decimal (in kg) for weight.',
            'muac': 'Please send a positive decimal (in cm) for mid-upper arm circumference.',
        }
        self.messages.update(kwargs.pop('messages', {}))

        if 'error_class' not in kwargs:
            kwargs['error_class'] = PlainErrorList
        super(CreateReportForm, self).__init__(*args, **kwargs)

        for field in self.messages:
            for msg_type in ('required', 'invalid', 'min_value'):
                self.fields[field].error_messages[msg_type] = self.messages[field]

    def clean_patient_id(self):
        val = self.cleaned_data['patient_id']
        # TODO - Validate that patient is registered and active.
        return val

    def clean(self):
        cleaned_data = super(CreateReportForm, self).clean()
        self.healthworker_id = 'placeholder'
        # TODO - Validate that connection is a registered and active healthworker.
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

