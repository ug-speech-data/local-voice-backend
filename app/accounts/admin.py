import os
from django.contrib import admin

from accounts.models import User
from django.contrib.auth.models import Permission

admin.site.register(User)

# Create default admin user
SUPER_ADMIN_USERNAME = os.environ.get("SUPER_ADMIN_USERNAME",
                                      "admin@gmail.com")
SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "admin")
try:
    superuser = User.objects.filter(email_address=SUPER_ADMIN_USERNAME,
                                    is_superuser=True).first()
    permissions = Permission.objects.all()
    if not superuser:
        superuser = User.objects.create_superuser(
            SUPER_ADMIN_USERNAME, password=SUPER_ADMIN_PASSWORD)
        print(f"Created superuser: {superuser}")
    else:
        print("Admin already exists")

    superuser.user_permissions.set(permissions)
    superuser.save()

except Exception as e:
    print(f"Error creating superuser: {e}")
