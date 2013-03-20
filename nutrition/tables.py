from __future__ import unicode_literals
from urllib import urlencode

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from nutrition.models import Report


class NutritionReportTable(tables.Table):
    # Override lots of columns to create better column labels.
    age = tables.Column(verbose_name='Age (Months)')
    reporter_id = tables.Column(verbose_name='Reporter')
    patient_id = tables.Column(verbose_name='Patient')

    class Meta:
        model = Report
        exclude = ('updated_date',)
        sequence = ('id', 'created_date', 'reporter_id', 'patient_id',
                'age', 'height', 'weight', 'muac', 'oedema',
                'weight4age', 'height4age', 'weight4height', 'status')

    def _build_filter_link(self, **kwargs):
        """Returns a link to the reports page filtered by kwargs."""
        base = reverse('nutrition_reports')
        get_params = urlencode(kwargs)
        return '{0}?{1}'.format(base, get_params)

    def render_created_date(self, value):
        return value.date()

    def render_reporter_id(self, value, record):
        """Link to a filtered reports page showing only this reporter."""
        data = {
            'link': self._build_filter_link(reporter_id=value),
            'name': record.reporter['name'] if record.reporter else None,
            'id': value,
        }
        return mark_safe('<a href="{link}">{name} ({id})</a>'.format(**data))

    def render_oedema(self, record):
        return record.get_oedema_display()

    def render_patient_id(self, value, record):
        """Link to a filtered reports page showing only this patient."""
        data = {
            'link': self._build_filter_link(patient_id=value),
            'name': record.patient['name'] if record.patient else None,
            'id': value,
        }
        return mark_safe('<a href="{link}">{name} ({id})</a>'.format(**data))

    def render_status(self, value, record):
        """Link to a filtered reports page showing only this status."""
        data = {
            'link': self._build_filter_link(status=record.status),
            'text': value,
        }
        return mark_safe('<a href="{link}">{text}</a>'.format(**data))
