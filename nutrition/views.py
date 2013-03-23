from __future__ import unicode_literals
import csv
import re

from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateView

from nutrition.forms import ReportFilterForm
from nutrition.models import Report
from nutrition.tables import NutritionReportTable


class NutritionReportMixin(object):
    """Allow filtering by patient, reporter, and status."""
    ordering = ['-created_date']  # Default order in which to display reports.

    @method_decorator(permission_required('nutrition.view_report'))
    def dispatch(self, request, *args, **kwargs):
        self.form = ReportFilterForm(self.request.GET)
        if self.form.is_valid():
            self.reports = self.form.get_reports(ordering=self.ordering)
        else:
            self.reports = Report.objects.none()
        return super(NutritionReportMixin, self).dispatch(request, *args,
                **kwargs)


class NutritionReportList(NutritionReportMixin, TemplateView):
    """Displays a paginated list of all nutrition reports."""
    template_name = 'nutrition/report_list.html'
    table_template_name = 'django_tables2/bootstrap-tables.html'
    reports_per_page = 10

    @property
    def page(self):
        return self.request.GET.get('page', 1)

    def get_context_data(self, *args, **kwargs):
        reports_table = NutritionReportTable(self.reports,
                template=self.table_template_name)
        reports_table.paginate(page=self.page, per_page=self.reports_per_page)
        return {
            'form': self.form,
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
        if not self.form.is_valid():
            url = reverse('nutrition_reports')
            if request.GET:
                url = '{0}?{1}'.format(url, request.GET.urlencode())
            return HttpResponseRedirect(url)
        response = HttpResponse(content_type='text/csv')
        content_disposition = 'attachment; filename=%s.csv' % self.filename
        response['Content-Disposition'] = content_disposition
        writer = csv.writer(response)
        for row in self.get_data():
            writer.writerow(row)
        return response

    def get_data(self):
        rows = [self.column_titles]  # Column titles are first row.
        for report in self.reports:
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
