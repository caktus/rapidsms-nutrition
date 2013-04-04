from __future__ import unicode_literals
from cStringIO import StringIO
import datetime
from urllib import urlencode

from nutrition.unicsv import UnicodeCSVReader

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from healthcare.api import client

from ..views import CSVNutritionReportList, NutritionReportList
from ..models import Report
from .base import NutritionTestBase


__all__ = ['NutritionReportListViewTest', 'CSVNutritionReportListViewTest']


class NutritionViewTest(NutritionTestBase):
    url_name = None
    perm_names = []
    url_args = []
    url_kwargs = {}
    get_kwargs = {}

    def setUp(self):
        super(NutritionViewTest, self).setUp()
        self.username = 'testuser'
        self.password = 'password'
        self.permissions = self.get_permissions()
        self.user = self.create_user(self.username, self.password,
                user_permissions=self.permissions)
        self.client.login(username=self.username, password=self.password)

    def get_permissions(self, perm_names=None):
        """Returns a list of Permission objects corresponding to perm_names."""
        perm_names = perm_names if perm_names is not None else self.perm_names
        return [Permission.objects.filter(content_type__app_label=app_label,
                codename=codename)[0] for app_label, codename in perm_names]

    def _url(self, url_name=None, url_args=None, url_kwargs=None,
            get_kwargs=None):
        url_name = url_name or self.url_name
        url_args = self.url_args if url_args is None else url_args
        url_kwargs = self.url_kwargs if url_kwargs is None else url_kwargs
        get_kwargs = self.get_kwargs if get_kwargs is None else get_kwargs
        url = reverse(url_name, args=url_args, kwargs=url_kwargs)
        if get_kwargs:
            url = '{0}?{1}'.format(url, urlencode(get_kwargs))
        return url

    def _get(self, url_name=None, url_args=None, url_kwargs=None,
            get_kwargs=None, url=None, *args, **kwargs):
        """Convenience wrapper for self.client.get.

        If url is not given, it is built using url_name, url_args, and
        url_kwargs. Get parameters may be added from get_kwargs.
        """
        url = url or self._url(url_name, url_args, url_kwargs, get_kwargs)
        return self.client.get(url, *args, **kwargs)


class NutritionReportListViewTest(NutritionViewTest):
    url_name = 'nutrition_reports'
    perm_names = [('nutrition', 'view_report')]

    def _extract(self, response):
        """Extract the information we're interested in from the context."""
        form = response.context['form']
        queryset = response.context['table'].data.queryset
        return queryset, form

    def test_no_permission(self):
        """Permission is required to get the nutrition reports list page."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 302)  # redirect to login

    def test_no_reports(self):
        """Retrieve the nutrition reports list when there are no reports."""
        Report.objects.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)

    def test_report(self):
        """Retrieve the nutrition reports list when there is one report."""
        report = self.create_report()
        response = self._get()
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report)

    def test_pagination(self):
        """The reports list should show 20 items per page."""
        for i in range(21):
            self.create_report()
        response = self._get(get_kwargs={'page': 2})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 21)
        page = response.context['table'].page
        self.assertEquals(page.object_list.data.count(), 1)

    def test_filter_reporter(self):
        """Reports should be filtered by reporter."""
        params = {'reporter_id': 'hello'}
        report = self.create_report(**params)
        other = self.create_report()
        response = self._get(get_kwargs=params)
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report)

    def test_filter_bad_reporter(self):
        """Form does no validation on reporter, but no results returned."""
        report = self.create_report()
        response = self._get(get_kwargs={'reporter_id': 'bad'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertFalse(form.errors)

    def test_filter_patient(self):
        """Reports should be filtered by patient."""
        report = self.create_report()
        other = self.create_report()
        params = {'patient_id': report.patient_id}
        response = self._get(get_kwargs=params)
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report)

    def test_filter_bad_patient(self):
        """Form does no validation on patient, but no results returned."""
        report = self.create_report()
        response = self._get(get_kwargs={'patient_id': 'bad'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertFalse(form.errors)

    def test_filter_status(self):
        """Reports should be filtered by status."""
        params = {'status': 'A'}
        report = self.create_report(analyze=False, **params)
        other = self.create_report(analyze=False, status='B')
        response = self._get(get_kwargs=params)
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report)

    def test_filter_bad_status(self):
        """Form has error & no results returned if invalid status is given."""
        report = self.create_report()
        response = self._get(get_kwargs={'status': 'bad'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('status' in form.errors)

    def test_filter_start_date(self):
        """Reports should be filtered by start date."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'start_date': '01/04/2010'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report2)

    def test_filter_bad_start_date(self):
        """Form has error & no results returned if start date is invalid."""
        report = self.create_report(data_date=datetime.date(2010, 1, 3))
        response = self._get(get_kwargs={'start_date': 'bad_date'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('start_date' in form.errors)

    def test_filter_end_date(self):
        """Reports should be filtered by end date."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'end_date': '01/04/2010'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report1)

    def test_filter_bad_end_date(self):
        """Form has error & no results returned if end date is invalid."""
        report = self.create_report(data_date=datetime.date(2010, 1, 3))
        response = self._get(get_kwargs={'end_date': 'bad_date'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('end_date' in form.errors)

    def test_filter_date_range(self):
        """Reports should be filtered by date range."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 1))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report3 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'start_date': '01/02/2010',
                'end_date': '01/04/2010'})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report2)

    def test_filter_bad_date_range(self):
        """Form has error & no results returned if date range is invalid."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 1))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report3 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'start_date': '01/04/2010',
                'end_date': '01/02/2010'})  # reversed
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue(form.non_field_errors())


class CSVNutritionReportListViewTest(NutritionViewTest):
    url_name = 'csv_nutrition_reports'
    perm_names = [('nutrition', 'view_report')]

    def _extract(self, response):
        reader = UnicodeCSVReader(StringIO(response.content))
        return [line for line in reader]

    def _check_report(self, response, *reports):
        self.assertEquals(response.status_code, 200)
        csv = self._extract(response)
        self.assertEquals(len(csv), 1 + len(reports))  # include headers row

        num_columns = 17
        headers, data = csv[0], csv[1:]
        self.assertEquals(len(headers), num_columns)
        for line in data:
            self.assertEquals(len(line), num_columns)
            pk = line[0]
            report = Report.objects.get(pk=pk)
            self.assertTrue(report in reports)

    def test_no_permissions(self):
        """Permission is required to export a nutrition reports list."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 302)  # redirect to login

    def test_no_reports(self):
        """Export reports list when there are no reports."""
        Report.objects.all().delete()
        response = self._get()
        self._check_report(response)

    def test_report(self):
        """Export reports list when there is one report."""
        report = self.create_report()
        response = self._get()
        self._check_report(response, report)

    def test_filter_reporter(self):
        """Reports export should be filtered by reporter."""
        params = {'reporter_id': 'hello'}
        report = self.create_report(**params)
        other = self.create_report()
        response = self._get(get_kwargs=params)
        self._check_report(response, report)

    def test_filter_bad_reporter(self):
        """Form does no validation on reporter, but no results returned."""
        report = self.create_report()
        response = self._get(get_kwargs={'reporter_id': 'bad'})
        self._check_report(response)

    def test_filter_patient(self):
        """Reports export should be filtered by patient."""
        report = self.create_report()
        other = self.create_report()
        params = {'patient_id': report.patient_id}
        response = self._get(get_kwargs=params)
        self._check_report(response, report)

    def test_filter_bad_patient(self):
        """Form does no validation on patient, but no results returned."""
        report = self.create_report()
        response = self._get(get_kwargs={'patient_id': 'bad'})
        self._check_report(response)

    def test_filter_status(self):
        """Reports export should be filtered by status."""
        params = {'status': 'A'}
        report = self.create_report(analyze=False, **params)
        other = self.create_report(analyze=False, status='B')
        response = self._get(get_kwargs=params)
        self._check_report(response, report)

    def test_filter_bad_status(self):
        """Invalid status causes redirect to regular list view."""
        report = self.create_report()
        response = self._get(get_kwargs={'status': 'bad'}, follow=True)
        correct_url = reverse('nutrition_reports') + '?status=bad'
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('status' in form.errors)

    def test_filter_start_date(self):
        """Reports should be filtered by start date."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'start_date': '01/04/2010'})
        self.assertEquals(response.status_code, 200)
        self._check_report(response, report2)

    def test_filter_bad_start_date(self):
        """Form has error & no results returned if start date is invalid."""
        report = self.create_report(data_date=datetime.date(2010, 1, 3))
        response = self._get(get_kwargs={'start_date': 'bad_date'},
                follow=True)
        correct_url = reverse('nutrition_reports') + '?start_date=bad_date'
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('start_date' in form.errors)

    def test_filter_end_date(self):
        """Reports should be filtered by end date."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'end_date': '01/04/2010'})
        self.assertEquals(response.status_code, 200)
        self._check_report(response, report1)

    def test_filter_bad_end_date(self):
        """Form has error & no results returned if end date is invalid."""
        report = self.create_report(data_date=datetime.date(2010, 1, 3))
        response = self._get(get_kwargs={'end_date': 'bad_date'},
                follow=True)
        correct_url = reverse('nutrition_reports') + '?end_date=bad_date'
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('end_date' in form.errors)

    def test_filter_date_range(self):
        """Reports should be filtered by date range."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 1))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report3 = self.create_report(data_date=datetime.date(2010, 1, 5))
        response = self._get(get_kwargs={'start_date': '01/02/2010',
                'end_date': '01/04/2010'})
        self._check_report(response, report2)

    def test_filter_bad_date_range(self):
        """Form has error & no results returned if date range is invalid."""
        report1 = self.create_report(data_date=datetime.date(2010, 1, 1))
        report2 = self.create_report(data_date=datetime.date(2010, 1, 3))
        report3 = self.create_report(data_date=datetime.date(2010, 1, 5))
        params = {'start_date': '01/04/2010', 'end_date': '01/02/2010'}
        response = self._get(get_kwargs=params, follow=True)  # reversed
        correct_url = '{0}?{1}'.format(reverse('nutrition_reports'),
                urlencode(params))
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue(form.non_field_errors())

