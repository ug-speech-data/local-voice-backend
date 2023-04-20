import decimal
import logging
from functools import reduce

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .managers import UserManager

logger = logging.getLogger("app")

#yapf: disable


class User(AbstractBaseUser, PermissionsMixin):
    email_address = models.EmailField(unique=True)
    photo = models.ImageField(upload_to="users", null=True, blank=True)
    surname = models.CharField(max_length=200, null=True, blank=True)
    other_names = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    phone_network = models.CharField(max_length=20, null=True, blank=True)
    age = models.IntegerField(blank=True, null=True)
    last_login_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    wallet = models.OneToOneField("Wallet", related_name="owner", on_delete=models.SET_NULL, null=True, blank=True)
    locale = models.CharField(max_length=20, default="", null=True, blank=True)
    gender = models.CharField(max_length=20, default="", null=True, blank=True)
    recording_environment = models.CharField(max_length=20, default="", null=True, blank=True)
    assigned_image_batch = models.IntegerField(default=-1, blank=True, null=True)
    assigned_audio_batch = models.IntegerField(default=-1, blank=True, null=True)
    accepted_privacy_policy = models.BooleanField(default=False)
    created_by = models.ForeignKey("User", related_name="created_users", on_delete=models.PROTECT, null=True, blank=True)
    updated_by = models.ForeignKey("User", related_name="updated_users", on_delete=models.PROTECT, null=True, blank=True)
    estimated_deduction_amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    device_ids = models.CharField(max_length=200, null=True, blank=True)
    lead = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    restricted_audio_count = models.IntegerField(default=10)
    reference_code = models.IntegerField(null=True, blank=True)
    audios_submitted = models.IntegerField(default=0)
    audios_validated = models.IntegerField(default=0)
    audios_rejected = models.IntegerField(default=0)
    audios_pending = models.IntegerField(default=0)
    audios_accepted = models.IntegerField(default=0)
    conflicts_resolved = models.IntegerField(default=0)

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

    @property
    def language(self):
        if not self.locale: return ""

        if "ee_gh" in self.locale:
            return "Ewe"
        elif "ak_gh" in self.locale:
            return "Akan"
        elif "dag_gh" in self.locale:
            return "Dagaare"
        elif "dga_gh" in self.locale:
            return "Dagbani"
        elif "kpo_gh" in self.locale:
            return "Ikposo"

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query}) for key in ["email_address", "surname", "other_names"]]
        return reduce(lambda x, y: x | y, queries)

    def __str__(self):
        return self.email_address


class Wallet(models.Model):
    total_payout = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))
    accrued_amount = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Miscelanous/Break down -- All in cedis
    validation_benefit = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))
    recording_benefit = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))
    transcription_benefit = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal(0.0))

    def __str__(self):
        if hasattr(self, "owner"):
            return str(self.owner.get_name())
        return "None"

    def save(self, *args, **kwargs) -> None:
        self.balance = self.accrued_amount - self.total_payout
        return super().save(*args, **kwargs)

    def credit_wallet(self, amount):
        self.accrued_amount += decimal.Decimal(amount)
        self.save()

    def set_validation_benefit(self, amount):
        self.validation_benefit = decimal.Decimal(amount)
        self.save()

    def set_recording_benefit(self, amount):
        self.recording_benefit = decimal.Decimal(amount)
        self.save()

    def set_transcription_benefit(self, amount):
        self.transcription_benefit = decimal.Decimal(amount)
        self.save()

    def set_accrued_amount(self, amount):
        self.accrued_amount = decimal.Decimal(amount)
        self.save()

    def increase_payout_amount(self, amount):
        self.total_payout += decimal.Decimal(amount)
        self.save()


class ActivityLog(models.Model):
    username = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_in_mills = models.IntegerField(default=0)

    def __str__(self) -> str:
        return "%s %s [%sms]" % (self.username, self.action, self.duration_in_mills)
