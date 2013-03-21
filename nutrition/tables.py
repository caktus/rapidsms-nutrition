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
        exclude = ('updated_date', 'global_patient_id', 'global_reporter_id')
        sequence = ('id', 'created_date', 'reporter_id', 'patient_id',
                'age', 'height', 'weight', 'muac', 'oedema',
                'weight4age', 'height4age', 'weight4height', 'status')

    def render_created_date(self, value):
        return value.date()

    def render_reporter_id(self, value, record):
        if record.reporter and record.reporter.get('name', None):
            return '{0} ({1})'.format(record.reporter['name'], value)
        return value

    def render_oedema(self, record):
        return record.get_oedema_display()

    def render_patient_id(self, value, record):
        if record.patient and record.patient.get('name', None):
            return '{0} ({1})'.format(record.patient['name'], value)
        return value
