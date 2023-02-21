import os

from django.db import models
from django.dispatch import receiver

from .models import User, Wallet


@receiver(models.signals.post_save, sender=User)
def auto_create_wallet(sender, instance, **kwargs):
    if instance.wallet == None:
        instance.wallet = Wallet.objects.create()
