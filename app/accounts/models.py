from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email_address = models.EmailField(unique=True)
    photo = models.ImageField(upload_to="users", null=True, blank=True)
    surname = models.CharField(max_length=200, null=True, blank=True)
    other_names = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    last_login_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Django stuff for authentication
    USERNAME_FIELD = "email_address"
    objects = UserManager()
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "users"
        permissions = [
            ("view_dashboard", "View Dashboard"),
        ]

    def get_name(self):
        return self.fullname or self.email_address

    def __str__(self):
        return self.email_address


class Participant(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True)
    local_id = models.IntegerField(default=0)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "participants"

    def __str__(self) -> str:
        return str(self.id)
