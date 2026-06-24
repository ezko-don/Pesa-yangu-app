"""URL configuration for the Pesa Yangu backend."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok", "service": "pesa-yangu-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("finances.urls")),
    path("api/hela/", include("hela.urls")),
]
