import logging
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager
from functools import reduce
import decimal
from django.db.models import Q

logger = logging.getLogger("app")

#yapf: disable


class User(AbstractBaseUser, PermissionsMixin):
    email_address = models.EmailField(unique=True)
    photo = models.ImageField(upload_to="users", null=True, blank=True)
    surname = models.CharField(max_length=200, null=True, blank=True)
    other_names = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    phone_network = models.CharField(max_length=20, null=True, blank=True)
    last_login_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey("Wallet", related_name="owner", on_delete=models.SET_NULL, null=True, blank=True)
    locale = models.CharField(max_length=20, default="", null=True, blank=True)
    assigned_image_batch = models.IntegerField(default=-1, blank=True, null=True)
    assigned_audio_batch = models.IntegerField(default=-1, blank=True, null=True)

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

    @property
    def fullname(self):
        return f"{self.surname} {self.other_names}"

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query}) for key in ["email_address", "surname", "other_names"]]
        return reduce(lambda x, y: x | y, queries)

    def __str__(self):
        return self.email_address


class Wallet(models.Model):
    total_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    accrued_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.owner)

    def save(self, *args, **kwargs) -> None:
        self.balance = self.accrued_amount - self.total_payout
        return super().save(*args, **kwargs)

    def credit_wallet(self, amount):
        self.accrued_amount += decimal.Decimal(amount)
        self.save()

    def increase_payout_amount(self, amount):
        self.total_payout += decimal.Decimal(amount)
        self.save()


class ActivityLog(models.Model):
    username = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return "%s %s" % (self.username, self.action)
