from __future__ import unicode_literals
import re

from nutrition.unicsv import UnicodeCSVWriter

from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateView

from django_tables2 import RequestConfig

from nutrition.forms import ReportFilterForm
from nutrition.tables import NutritionReportTable, CSVNutritionReportTable


class NutritionReportMixin(object):
    """Allow filtering by patient, reporter, and status."""

    @method_decorator(permission_required('nutrition.view_report'))
    def dispatch(self, request, *args, **kwargs):
        self.form = ReportFilterForm(request.GET)
        self.items = self.form.get_items()
        return super(NutritionReportMixin, self).dispatch(request, *args,
                **kwargs)


class NutritionReportList(NutritionReportMixin, TemplateView):
    """Displays a paginated list of all nutrition reports."""
    template_name = 'nutrition/report_list.html'
    table_template_name = 'django_tables2/bootstrap-tables.html'
    items_per_page = 20

    def get_table(self):
        table = NutritionReportTable(self.items,
                template=self.table_template_name)
        paginate = {'per_page': self.items_per_page}
        RequestConfig(self.request, paginate=paginate).configure(table)
        return table

    def get_context_data(self, *args, **kwargs):
        return {
            'form': self.form,
            'table': self.get_table(),
        }


class CSVNutritionReportList(NutritionReportMixin, View):
    """Export filtered reports to a CSV file."""
    filename = 'nutrition_reports'

    def get_table(self):
        table = CSVNutritionReportTable(self.items)
        RequestConfig(self.request).configure(table)
        return table

    def get(self, request, *args, **kwargs):
        # Redirect to the plain reports list if form is invalid.
        if not self.form.is_valid():
            url = reverse('nutrition_reports')
            if request.GET:
                url = '{0}?{1}'.format(url, request.GET.urlencode())
            return HttpResponseRedirect(url)

        response = HttpResponse(content_type='text/csv')
        content_disposition = 'attachment; filename=%s.csv' % self.filename
        response['Content-Disposition'] = content_disposition
        writer = UnicodeCSVWriter(response)
        writer.writerows(self.get_rows())
        return response

    def get_rows(self):
        table = self.get_table()
        headers = [col.title() for col in table.columns.names()]
        rows = [headers]
        for item in table.rows:
            row = []
            for cell in item:
                row.append(cell)
            rows.append(row)
        return rows
