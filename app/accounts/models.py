import logging
from random import sample

import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from setup.models import SysConfig

from .managers import UserManager

logger = logging.getLogger("app")


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


class Otp(models.Model):

    def get_pin():
        return "".join(
            sample(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"], 6))

    address = models.CharField(max_length=100)
    pin = models.CharField(max_length=10, default=get_pin)
    duration = models.IntegerField(default=3)
    created_at = models.DateTimeField(default=timezone.now)
    delivered = models.BooleanField(default=False)

    def validate(self, pin):
        return not self.expired() and pin == self.pin

    def send_sms(self):
        number = self.address
        config = SysConfig.objects.first()
        sender_id = config.sms_sender_id
        api_key = config.api_key or settings.ARKESEL_API
        message = f"Your authorization PIN/OTP is {self.pin}"
        url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key={api_key}&to={number}&from={sender_id}&sms={message}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.delivered = True
                self.save()
                return True
        except Exception as e:
            logger.error(str(e))
        return False

    def get_time_left(self):
        return max(
            0.01,
            round((self.created_at + timedelta(minutes=self.duration) -
                   timezone.now()).total_seconds(), 2))

    def expired(self):
        return timezone.now() > self.created_at + timedelta(
            minutes=self.duration)


class ActivityLog(models.Model):
    username = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return "%s %s" % (self.username, self.action)
