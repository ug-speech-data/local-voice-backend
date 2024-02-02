from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# yapf: disable
urlpatterns = [
    path('/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('rest_api.urls')),
    path('payments/', include('payments.urls')),
    path("admin/", admin.site.urls),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize django admin page.
admin.site.site_header = "LOCAL VOICE APP ADMINISTRATION"  # default: "Django Administration"
admin.site.index_title = "Site Administration"  # default: "Site administration"
admin.site.site_title = 'Local Voice site admin'  # default: "Django site admin"
