from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("report/excel/", views.generate_report_excel, name="report_excel"),
    path("report/pdf/", views.generate_report_pdf, name="report_pdf"),
]
