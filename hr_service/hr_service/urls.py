from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import home_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("accounts/", include("accounts.urls")),
    path("documents/", include("documents.urls")),
    path("chat/", include("chat.urls")),
    path("vacancies/", include("vacancies.urls")),
    path("analytics/", include("analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
