from __future__ import unicode_literals
from urllib import urlencode

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from healthcare.api import client

from ..views import CSVNutritionReportList, NutritionReportList
from ..models import Report
from .base import NutritionTestBase


__all__ = ['NutritionReportListViewTest', 'NutritionReportExportViewTest']


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
        queryset = response.context['reports_table'].data.queryset
        filters = response.context['filters']
        return queryset, filters

    def test_no_permission(self):
        """Permission is required to get the nutrition reports list page."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_no_reports(self):
        """Retrieve the nutrition reports list when there are no reports."""
        Report.objects.all().delete()
        response = self._get()
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 0)
        self.assertEqual(filters, {})

    def test_report(self):
        """Retrieve the nutrition reports list when there is one report."""
        report = self.create_report()
        response = self._get()
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.get(), report)
        self.assertEqual(filters, {})

    def test_pagination(self):
        """The reports list should show 10 items per page."""
        for i in range(11):
            self.create_report()
        response = self._get(get_kwargs={'page': 2})
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 11)
        self.assertEqual(filters, {})
        page = response.context['reports_table'].page
        self.assertEqual(page.object_list.data.count(), 1)

    def test_filter_reporter(self):
        """Reports should be filtered by reporter."""
        params = {'reporter_id': 'hello'}
        report = self.create_report(**params)
        other = self.create_report()
        response = self._get(get_kwargs=params)
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.get(), report)
        self.assertEqual(filters, params)

    def test_filter_patient(self):
        """Reports should be filtered by patient."""
        params = {'patient_id': 'hello'}
        report = self.create_report(**params)
        other = self.create_report()
        response = self._get(get_kwargs=params)
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.get(), report)
        self.assertEqual(filters, params)

    def test_filter_status(self):
        """Reports should be filtered by status."""
        params = {'status': 'A'}
        report = self.create_report(analyze=False, **params)
        other = self.create_report(analyze=False, status='B')
        response = self._get(get_kwargs=params)
        self.assertEqual(response.status_code, 200)
        queryset, filters = self._extract(response)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.get(), report)
        self.assertEqual(filters, params)


class NutritionReportExportViewTest(NutritionViewTest):
    url_name = 'csv_nutrition_reports'
    perm_names = [('nutrition', 'view_report')]

    def _extract(self, response):
        content = response.content.strip()
        return [line.split(',') for line in content.split('\r\n')]

    def _check_report(self, response, *reports):
        self.assertEqual(response.status_code, 200)
        csv = self._extract(response)
        self.assertEqual(len(csv), 1 + len(reports))  # include headers row

        num_columns = 15
        headers, data = csv[0], csv[1:]
        self.assertEqual(len(headers), num_columns)
        for line in data:
            self.assertEqual(len(line), num_columns)
            pk = line[0]
            report = Report.objects.get(pk=pk)
            self.assertTrue(report in reports)

    def test_no_permissions(self):
        """Permission is required to export a nutrition reports list."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEqual(response.status_code, 302)  # redirect to login

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

    def test_filter_patient(self):
        """Reports export should be filtered by patient."""
        params = {'patient_id': 'hello'}
        report = self.create_report(**params)
        other = self.create_report()
        response = self._get(get_kwargs=params)
        self._check_report(response, report)

    def test_filter_status(self):
        """Reports export should be filtered by status."""
        params = {'status': 'A'}
        report = self.create_report(analyze=False, **params)
        other = self.create_report(analyze=False, status='B')
        response = self._get(get_kwargs=params)
        self._check_report(response, report)
