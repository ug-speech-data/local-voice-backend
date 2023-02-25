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

        old_participant_privacy_statement_audio_ewe = AppConfiguration.objects.get(
            pk=instance.pk).participant_privacy_statement_audio_ewe

        old_participant_privacy_statement_audio_akan = AppConfiguration.objects.get(
            pk=instance.pk).participant_privacy_statement_audio_akan

        old_participant_privacy_statement_audio_dagaare = AppConfiguration.objects.get(
            pk=instance.pk).participant_privacy_statement_audio_dagaare

        old_participant_privacy_statement_audio_ikposo = AppConfiguration.objects.get(
            pk=instance.pk).participant_privacy_statement_audio_ikposo

        old_participant_privacy_statement_audio_dagbani = AppConfiguration.objects.get(
            pk=instance.pk).participant_privacy_statement_audio_dagbani

    except AppConfiguration.DoesNotExist:
        return False

    # Delete old video
    new_demo_video = instance.demo_video
    if not old_demo_video == new_demo_video and old_demo_video:
        if os.path.isfile(old_demo_video.path):
            os.remove(old_demo_video.path)

    # Android APK
    new_android_apk = instance.android_apk
    if not old_android_apk == new_android_apk and old_android_apk:
        if os.path.isfile(old_android_apk.path):
            os.remove(old_android_apk.path)

    # Delete old ewe audio
    new_participant_privacy_statement_audio_ewe = instance.participant_privacy_statement_audio_ewe
    if not old_participant_privacy_statement_audio_ewe == new_participant_privacy_statement_audio_ewe and old_participant_privacy_statement_audio_ewe:
        if os.path.isfile(old_participant_privacy_statement_audio_ewe.path):
            os.remove(old_participant_privacy_statement_audio_ewe.path)

    # Delete old dagaare audio
    new_participant_privacy_statement_audio_dagaare = instance.participant_privacy_statement_audio_dagaare
    if not old_participant_privacy_statement_audio_dagaare == new_participant_privacy_statement_audio_dagaare and old_participant_privacy_statement_audio_dagaare:
        if os.path.isfile(
                old_participant_privacy_statement_audio_dagaare.path):
            os.remove(old_participant_privacy_statement_audio_dagaare.path)

    # Delete old dagbani audio
    new_participant_privacy_statement_audio_dagbani = instance.participant_privacy_statement_audio_dagbani
    if not old_participant_privacy_statement_audio_dagbani == new_participant_privacy_statement_audio_dagbani and old_participant_privacy_statement_audio_dagbani:
        if os.path.isfile(
                old_participant_privacy_statement_audio_dagbani.path):
            os.remove(old_participant_privacy_statement_audio_dagbani.path)

    # Delete old akan audio
    new_participant_privacy_statement_audio_akan = instance.participant_privacy_statement_audio_akan
    if not old_participant_privacy_statement_audio_akan == new_participant_privacy_statement_audio_akan and old_participant_privacy_statement_audio_akan:
        if os.path.isfile(old_participant_privacy_statement_audio_akan.path):
            os.remove(old_participant_privacy_statement_audio_akan.path)

    # Delete old ikposo audio
    new_participant_privacy_statement_audio_ikposo = instance.participant_privacy_statement_audio_ikposo
    if not old_participant_privacy_statement_audio_ikposo == new_participant_privacy_statement_audio_ikposo and old_participant_privacy_statement_audio_ikposo:
        if os.path.isfile(old_participant_privacy_statement_audio_ikposo.path):
            os.remove(old_participant_privacy_statement_audio_ikposo.path)
