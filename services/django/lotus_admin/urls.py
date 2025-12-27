from core.admin import admin_site
from django.urls import include, path

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("core.urls")),
]
