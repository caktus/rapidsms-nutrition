from __future__ import unicode_literals
from urllib import urlencode

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from nutrition.models import Report


class NutritionReportTable(tables.Table):
    # Override lots of columns to create better column labels.
    age = tables.Column(verbose_name='Age (Months)')
    sex = tables.Column()
    reporter_connection = tables.Column(verbose_name='Reporter')
    patient_id = tables.Column(verbose_name='Patient')

    class Meta:
        model = Report
        exclude = ('updated_date', 'global_patient_id', 'global_reporter_id',
                'raw_text')
        sequence = ('id', 'created_date', 'reporter_connection', 'patient_id',
                'age', 'sex', 'height', 'weight', 'muac', 'oedema',
                'weight4age', 'height4age', 'weight4height', 'status',
                'active')

    def render_active(self, value):
        return 'Active' if value else 'Cancelled'

    def render_created_date(self, value):
        return value.date()

    def render_oedema(self, record):
        return record.get_oedema_display()


class CSVNutritionReportTable(NutritionReportTable):

    class Meta:
        model = Report
        exclude = ('global_patient_id', 'global_reporter_id', 'raw_text')
        sequence = ('id', 'created_date', 'updated_date', 'reporter_connection',
                'patient_id', 'age', 'sex', 'height', 'weight', 'muac',
                'oedema', 'weight4age', 'height4age', 'weight4height',
                'status')


