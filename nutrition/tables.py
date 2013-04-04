from __future__ import unicode_literals

import django_tables2 as tables

from nutrition.models import Report


class NutritionReportTable(tables.Table):
    # Override lots of columns to create better column labels.
    age = tables.Column(verbose_name='Age (Months)', orderable=False)
    sex = tables.Column(orderable=False)
    location = tables.Column(orderable=False)
    reporter_id = tables.Column(verbose_name='Reporter')
    patient_id = tables.Column(verbose_name='Patient')

    class Meta:
        model = Report
        exclude = ('created', 'updated', 'global_patient_id', 'global_reporter_id',
                'raw_text')
        sequence = ('id', 'data_date', 'reporter_id', 'patient_id',
                'age', 'sex', 'location', 'height', 'weight', 'muac', 'oedema',
                'weight4age', 'height4age', 'weight4height', 'status',
                'active')

    def render_active(self, value):
        return 'Active' if value else 'Cancelled'

    def render_oedema(self, record):
        return record.get_oedema_display()


class CSVNutritionReportTable(NutritionReportTable):

    class Meta:
        model = Report
        exclude = ('created', 'global_patient_id', 'global_reporter_id',
                'raw_text')
        sequence = ('id', 'data_date', 'updated', 'reporter_id',
                'patient_id', 'age', 'sex', 'location', 'height', 'weight',
                'muac', 'oedema', 'weight4age', 'height4age', 'weight4height',
                'status')
