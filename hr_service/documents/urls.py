from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="document_list"),
    path("upload/", views.document_upload, name="document_upload"),
    path("<int:pk>/", views.document_detail, name="document_detail"),
    path("<int:pk>/review/", views.document_review, name="document_review"),
]
