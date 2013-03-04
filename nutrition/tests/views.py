from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from healthcare.api import client

from ..views import CSVNutritionReportList, NutritionReportList
from ..models import Report
from .base import NutritionTestBase


__all__ = ['NutritionReportListViewTest', 'NutritionReportExportViewTest']


class NutritionReportListViewTest(NutritionTestBase):
    pass


class NutritionReportExportViewTest(NutritionTestBase):
    pass
