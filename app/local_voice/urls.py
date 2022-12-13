
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('api/', include('rest_api.urls')),
    path("admin/", admin.site.urls),
]
