import os

from django.db import models
from django.dispatch import receiver

from setup.models import AppConfiguration

from .models import Audio, Image


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_image_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)


@receiver(models.signals.post_delete, sender=Audio)
def auto_delete_audio_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(models.signals.pre_save, sender=AppConfiguration)
def auto_delete_conf_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `AppConfiguration` object is updated
    with new file.
    """
    if not instance.pk:
        return False
    try:
        old_demo_video = AppConfiguration.objects.get(
            pk=instance.pk).demo_video
        old_android_apk = AppConfiguration.objects.get(
            pk=instance.pk).android_apk
    except AppConfiguration.DoesNotExist:
        return False

    new_demo_video = instance.demo_video
    if not old_demo_video == new_demo_video:
        if os.path.isfile(old_demo_video.path):
            os.remove(old_demo_video.path)

    # Android APK
    new_android_apk = instance.android_apk
    if not old_android_apk == new_android_apk:
        if os.path.isfile(old_android_apk.path):
            os.remove(old_android_apk.path)
