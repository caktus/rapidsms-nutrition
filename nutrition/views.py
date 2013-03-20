from __future__ import unicode_literals
import csv
import re

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateView

from nutrition.models import Report
from nutrition.tables import NutritionReportTable


class NutritionReportMixin(object):
    """Allow filtering by patient, reporter, and status."""
    # Default order by which reports should be displayed.
    ordering = ['-created_date']

    @method_decorator(permission_required('nutrition.view_report'))
    def dispatch(self, request, *args, **kwargs):
        return super(NutritionReportMixin, self).dispatch(request, *args,
                **kwargs)

    def get_filters(self):
        filters = {}
        if self.patient_id:
            filters['patient_id'] = self.patient_id
        if self.reporter_id:
            filters['reporter_id'] = self.reporter_id
        if self.status:
            filters['status'] = self.status
        return filters

    def get_reports(self, filters=None, ordering=None):
        """Returns filtered reports list."""
        filters = self.get_filters() if filters is None else filters
        ordering = self.ordering if ordering is None else ordering
        return Report.objects.filter(**filters).order_by(*ordering)

    @property
    def reporter_id(self):
        return self.request.GET.get('reporter_id', None)

    @property
    def patient_id(self):
        return self.request.GET.get('patient_id', None)

    @property
    def status(self):
        return self.request.GET.get('status', None)


class NutritionReportList(NutritionReportMixin, TemplateView):
    """Displays a paginated list of all nutrition reports."""
    template_name = 'nutrition/report_list.html'
    table_template_name = 'django_tables2/bootstrap-tables.html'
    reports_per_page = 10

    @property
    def page(self):
        return self.request.GET.get('page', 1)

    def get_context_data(self, *args, **kwargs):
        filters = self.get_filters()
        reports = self.get_reports(filters)
        reports_table = NutritionReportTable(reports,
                template=self.table_template_name)
        reports_table.paginate(page=self.page, per_page=self.reports_per_page)
        return {
            'filters': filters,
            'reports_table': reports_table,
        }


class CSVNutritionReportList(NutritionReportMixin, View):
    """Export filtered reports to a CSV file."""
    # Fields to include in the csv, in order.
    attrs = ('id', 'created_date', 'updated_date', 'reporter', 'patient',
            'age', 'sex', 'height', 'weight', 'muac', 'oedema',
            'weight4age', 'height4age', 'weight4height', 'status')
    filename = 'nutrition_reports'

    @property
    def column_titles(self):
        """Substitute non-alphanumeric characters with whitespace."""
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

    def render_reporter(self, report):
        """Custom rendering of reporter data."""
        if report.reporter:
            name = report.reporter.get('name', '')
            if name:
                return '{0} ({1})'.format(name, report.reporter_id)
            return report.reporter_id
        return None

    def render_patient(self, report):
        """Custom rendering of patient data."""
        if report.patient:
            name = report.patient.get('name', '')
            if name:
                return '{0} ({1})'.format(name, report.patient_id)
            return report.patient_id
        return None
