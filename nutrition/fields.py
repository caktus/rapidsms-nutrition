from __future__ import unicode_literals

from django import forms


class NullDecimalField(forms.fields.DecimalField):
    """
    Similar to a DecimalField, but interprets specific strings to mean None.
    """
    null_values = (None, 'x', 'xx', 'xxx')

    def __init__(self, null_values=None, *args, **kwargs):
        super(NullDecimalField, self).__init__(*args, **kwargs)
        if null_values is not None:
            self.null_values = null_values

    def to_python(self, value):
        val = value.strip().lower() if isinstance(value, basestring) else value
        if val in self.null_values:
            return None
        return super(NullDecimalField, self).to_python(value)


class NullYesNoWidget(forms.widgets.NullBooleanSelect):
    """Allows a wider variety of things to mean True or False."""
    # '2' is used by NullBooleanSelect.
    true_values = (True, 1, '2', 'yes', 'y', 'oui', 'o', 'true')
    # '3' is used by NullBooleanSelect.
    false_values = (False, 0, '3', 'no', 'n', 'non', 'false')
    null_values = (None, 'x', 'xx', 'xxx')

    def __init__(self, true_values=None, false_values=None, null_values=None,
            *args, **kwargs):
        super(NullYesNoWidget, self).__init__(*args, **kwargs)
        if true_values is not None:
            self.true_values = true_values
        if false_values is not None:
            self.false_values = false_values
        if nulL_values is not None:
            self.null_values = null_values

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)

        # Try to interpret the value as True, False, or None.
        val = value.strip().lower() if isinstance(value, basestring) else value
        if val in self.true_values:
            return True
        elif val in self.false_values:
            return False
        elif val in self.null_values:
            return None

        return value  # The value will be invalidated by the NullYesNoField.


class NullYesNoField(forms.fields.NullBooleanField):
    """
    Similar to a NullBooleanField, but raises a ValidationError if the value
    is not True, False, or None.
    """
    widget = NullYesNoWidget

    def to_python(self, value):
        if value in (True, False, None):
            return value
        raise forms.ValidationError(self.error_messages['invalid'])

    def _has_changed(self, initial, data):
        return initial != data
