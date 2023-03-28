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
        old_android_apk = AppConfiguration.objects.get(
            pk=instance.pk).android_apk

        # Demo videos
        old_demo_video_ewe = AppConfiguration.objects.get(
            pk=instance.pk).demo_video_ewe

        old_demo_video_akan = AppConfiguration.objects.get(
            pk=instance.pk).demo_video_akan

        old_demo_video_dagaare = AppConfiguration.objects.get(
            pk=instance.pk).demo_video_dagaare

        old_demo_video_ikposo = AppConfiguration.objects.get(
            pk=instance.pk).demo_video_ikposo

        old_demo_video_dagbani = AppConfiguration.objects.get(
            pk=instance.pk).demo_video_dagbani

        # Privacy statement audios
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

    # Delete old videos
    # Delete old ewe video
    new_demo_video_ewe = instance.demo_video_ewe
    if not old_demo_video_ewe == new_demo_video_ewe and old_demo_video_ewe:
        if os.path.isfile(old_demo_video_ewe.path):
            os.remove(old_demo_video_ewe.path)

    # Delete old dagaare video
    new_demo_video_dagaare = instance.demo_video_dagaare
    if not old_demo_video_dagaare == new_demo_video_dagaare and old_demo_video_dagaare:
        if os.path.isfile(old_demo_video_dagaare.path):
            os.remove(old_demo_video_dagaare.path)

    # Delete old dagbani video
    new_demo_video_dagbani = instance.demo_video_dagbani
    if not old_demo_video_dagbani == new_demo_video_dagbani and old_demo_video_dagbani:
        if os.path.isfile(old_demo_video_dagbani.path):
            os.remove(old_demo_video_dagbani.path)

    # Delete old akan video
    new_demo_video_akan = instance.demo_video_akan
    if not old_demo_video_akan == new_demo_video_akan and old_demo_video_akan:
        if os.path.isfile(old_demo_video_akan.path):
            os.remove(old_demo_video_akan.path)

    # Delete old ikposo video
    new_demo_video_ikposo = instance.demo_video_ikposo
    if not old_demo_video_ikposo == new_demo_video_ikposo and old_demo_video_ikposo:
        if os.path.isfile(old_demo_video_ikposo.path):
            os.remove(old_demo_video_ikposo.path)

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


@receiver(models.signals.pre_save, sender=Image)
def auto_delete_image_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_file = Image.objects.get(pk=instance.pk).file
        old_thumbnail = Image.objects.get(pk=instance.pk).thumbnail
    except Image.DoesNotExist:
        return False

    # Delete old image file
    new_file = instance.file
    if old_file != new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

    # Delete old thumbnail file
    new_thumbnail = instance.thumbnail
    if old_thumbnail != new_thumbnail and old_thumbnail:
        if os.path.isfile(old_thumbnail.path):
            os.remove(old_thumbnail.path)


@receiver(models.signals.pre_save, sender=Audio)
def auto_delete_audio_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False
    old_file_wav = None
    old_file_mp3 = None

    try:
        old_file_wav = Audio.objects.get(pk=instance.pk).file
    except Audio.DoesNotExist:
        pass

    try:
        old_file_mp3 = Audio.objects.get(pk=instance.pk).file_mp3
    except Audio.DoesNotExist:
        pass

    # Delete old audio file
    new_file_wav = instance.file
    new_file_mp3 = instance.file_mp3

    if old_file_mp3 != new_file_mp3 and old_file_mp3:
        if os.path.isfile(old_file_mp3.path):
            os.remove(old_file_mp3.path)

    if old_file_wav != new_file_wav and old_file_wav:
        if os.path.isfile(old_file_wav.path):
            os.remove(old_file_wav.path)
