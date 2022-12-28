from django.contrib import admin

from setup.models import SysConfig

# Default
try:
    if not SysConfig.objects.all():
        SysConfig.objects.create()
except Exception as e:
    pass
