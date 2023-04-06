from django.contrib import admin

from accounts.models import User, Wallet, ActivityLog

admin.site.register(User)
admin.site.register(Wallet)
admin.site.register(ActivityLog)
