from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^$',
        views.NutritionReportList.as_view(),
        name='nutrition_reports',
    ),
    url(r'^csv/$',
        views.CSVNutritionReportList.as_view(),
        name='csv_nutrition_reports',
    ),
)
