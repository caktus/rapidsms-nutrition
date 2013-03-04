from __future__ import unicode_literals
import csv
import re

from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView

from nutrition.models import Report
from nutrition.tables import NutritionReportTable


class NutritionReportMixin(object):
    """Allow filtering by patient and healthworker."""

    @property
    def patient_id(self):
        return self.request.GET.get('patient_id', None)

    @property
    def healthworker_id(self):
        return self.request.GET.get('healthworker_id', None)

    @property
    def status(self):
        return self.request.GET.get('status', None)

    def get_reports(self):
        """Returns Reports filtered by patient and healthworker."""
        reports = Report.objects.all()
        if self.patient_id:
            reports = reports.filter(patient_id=self.patient_id)
        if self.healthworker_id:
            reports = reports.filter(healthworker_id=self.healthworker_id)
        if self.status:
            reports = reports.filter(status=status)
        return reports.order_by('-created')


class NutritionReportList(NutritionReportMixin, TemplateView):
    """Displays a paginated list of all nutrition reports."""
    template_name = 'nutrition/report_list.html'
    table_template_name = 'django_tables2/bootstrap-tables.html'
    reports_per_page = 10

    @property
    def page(self):
        return self.request.GET.get('page', 1)

    def get_context_data(self, *args, **kwargs):
        reports = self.get_reports()
        reports_table = NutritionReportTable(reports,
                template=self.table_template_name)
        reports_table.paginate(page=self.page, per_page=self.reports_per_page)
        return {
            'healthworker_id': self.healthworker_id,
            'patient_id': self.patient_id,
            'status': self.status,
            'reports_table': reports_table,
        }


class CSVNutritionReportList(NutritionReportMixin, View):
    """Export filtered reports to a CSV file."""
    # Fields to include in the csv, in order.
    attrs = ('id', 'created', 'last_updated', 'healthworker', 'patient',
            'age', 'sex', 'height', 'weight', 'muac', 'oedema',
            'weight4age', 'height4age', 'weight4height', 'status')
    filename = 'nutrition_reports'

    @property
    def column_titles(self):
        p = re.compile('[^a-zA-Z0-9]')
        return [p.sub(' ', attr).title() for attr in self.attrs]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        content_disposition = 'attachment; filename=%s.csv' % self.filename
        response['Content-Disposition'] = content_disposition
        writer = csv.writer(response)
        for row in self.get_data():
            writer.writerow(row)
        return response

    def get_data(self):
        rows = [self.column_titles]  # Column titles are first row.
        for report in self.get_reports():
            row = []
            for attr in self.attrs:
                # Allow (optional) custom rendering of each column.
                render_attr = 'render_{0}'.format(attr)
                get_display = 'get_{0}_display'.format(attr)
                if hasattr(self, render_attr):
                    row.append(getattr(self, render_attr)(report))
                elif hasattr(report, get_display):
                    row.append(getattr(report, get_display)())
                else:
                    row.append(getattr(report, attr))
            rows.append(row)
        return rows

    def render_healthworker(self, report):
        return 'placeholder'  # TODO

    def render_patient(self, report):
        patient = report.patient
        if patient:
            return '{0} ({1})'.format(patient.get('name', ''),
                    report.patient_id)
        return ''
