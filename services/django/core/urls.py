from django.urls import path

from .admin import admin_site

urlpatterns = [
    path("", admin_site.urls),
]
