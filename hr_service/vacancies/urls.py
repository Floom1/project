from django.urls import path

from . import views

app_name = "vacancies"

urlpatterns = [
    path("", views.vacancy_list, name="vacancy_list"),
    path("create/", views.vacancy_create, name="vacancy_create"),
    path("<int:pk>/", views.vacancy_detail, name="vacancy_detail"),
    path("<int:pk>/edit/", views.vacancy_edit, name="vacancy_edit"),
    path("<int:pk>/apply/", views.vacancy_apply, name="vacancy_apply"),
    path("<int:pk>/stages/add/", views.stage_add, name="stage_add"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("interviews/", views.interview_list, name="interview_list"),
    path("interviews/<int:pk>/complete/", views.interview_complete, name="interview_complete"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("api/notifications/unread/", views.unread_notification_count, name="unread_notification_count"),
]
