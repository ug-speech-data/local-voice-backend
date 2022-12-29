from django.contrib import admin

from .models import AppConfiguration

admin.site.register(AppConfiguration)
# Default
try:
    if not AppConfiguration.objects.all():
        AppConfiguration.objects.create()
except Exception as e:
    pass
