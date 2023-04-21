from django.contrib import admin

from accounts.models import ActivityLog, User, Wallet

admin.site.register(User)
admin.site.register(Wallet)
admin.site.register(ActivityLog)
