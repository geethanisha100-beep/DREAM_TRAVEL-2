from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "TTAM Administration"
admin.site.index_title = "Dream Travel management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("travel.api")),
    path("", include("accounts.urls")),
    path("", include("travel.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
