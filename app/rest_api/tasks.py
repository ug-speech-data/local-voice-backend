import logging
import os
import zipfile
from datetime import datetime, timedelta

import ffmpeg
import pandas as pd
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db import NotSupportedError
from django.db.models import Count, Q

from accounts.models import User
from dashboard.models import (Audio, AudioTranscriptionAssignment,
                              AudioValidationAssignment, ExportTag,
                              Notification, Transcription)
from local_voice.utils.constants import TranscriptionStatus
from setup.models import AppConfiguration

logger = logging.getLogger("app")


@shared_task()
def export_audio_data(user_id, data, base_url):
    update_notification = Notification.objects.create(
        message="Data export started",
        title="Data Export",
        type="info",
        user_id=user_id)
    update_notification = Notification.objects.filter(
        id=update_notification.id)

    # Create temp directory
    temp = os.path.join(settings.MEDIA_ROOT, "temps")
    if not os.path.exists(temp):
        os.makedirs(temp)

    timestamp = str(datetime.today()).split(".")[0]
    output_filename = f"temps/export_audio_{timestamp}.zip"
    output_dir = settings.MEDIA_ROOT / output_filename

    columns = [
        'IMAGE_PATH',
        'IMAGE_SRC_URL',
        "AUDIO_PATH",
        'ORG_NAME',
        'PROJECT_NAME ',
        'SPEAKER_ID',
        "LOCALE",
        "TRANSCRIPTION",
        "GENDER",
        "AGE",
        "DEVICE",
        "ENVIRONMENT",
        "YEAR",
    ]
    rows = []
    audios = Audio.objects.filter(audio_status="accepted", deleted=False)

    # Apply filters
    status = data.get("status")
    tag = data.get("tag")
    locale = data.get("locale")
    number_of_files = data.get("number_of_files")
    number_of_files = int(number_of_files) if str(
        number_of_files).isdigit() else 0

    if tag:
        audios = audios.exclude(tags__tag=tag)

    if locale != "all":
        audios = audios.filter(locale=locale)

    if status == "transcription_resolved":
        audios = audios.filter(
            transcription_status=TranscriptionStatus.ACCEPTED.value)
    if status == "transcribed":
        audios = audios.annotate(t_count=Count("transcriptions")).filter(
            t_count__gt=0)

    audios = audios.order_by("id")
    if number_of_files > 0:
        audios = audios[:number_of_files]

    total_audios = audios.count()
    skip_count = 0
    with zipfile.ZipFile(output_dir,
                         'w',
                         compression=zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zip_file:
        for index, audio in enumerate(audios):
            if not (audio.file and audio.image and audio.image.file):
                continue
            try:
                message = f"{round((index + 1) / total_audios * 100, 2)}% Done: Writing audio {index + 1} of {total_audios}. Skipped {skip_count}"
                update_notification.update(message=message)
                # Copy audio and image files to temp directory
                audio_filename = audio.file_mp3.name if audio.file_mp3 else audio.file.name
                image_filename = audio.image.file.name
                new_image_filename = image_filename.split("/")[0] + "/" + str(
                    audio.image.id).zfill(4) + "." + image_filename.split(".")[-1]
                zip_file.write(
                    settings.MEDIA_ROOT / audio_filename,
                    arcname=f"assets/{audio.locale}_{audio_filename}")
                zip_file.write(settings.MEDIA_ROOT / image_filename,
                               arcname=f"assets/{new_image_filename}")

                participant = audio.participant
                transcriptions = "\n\n".join(audio.get_transcriptions())

                row = [
                    f"assets/{new_image_filename}",
                    audio.image.source_url,
                    f"assets/{audio.locale}_{audio_filename}",
                    "University of Ghana",
                    "Waxal",
                    participant.id if participant else audio.submitted_by.id,
                    audio.locale,
                    transcriptions,
                    participant.gender
                    if participant else audio.submitted_by.gender,
                    participant.age if participant else audio.submitted_by.age,
                    audio.device_id,
                    audio.environment,
                    audio.year,
                ]
                rows.append(row)
            except Exception as e:
                logger.error(str(e))
                skip_count += 1

        message = f"Writing excel file..."
        update_notification.update(message=message)

        # Write data to excel file
        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(temp + '/waxal-project-data.xlsx')
        zip_file.write(temp + '/waxal-project-data.xlsx',
                       arcname='waxal-project-data.xlsx')
        os.remove(temp + '/waxal-project-data.xlsx')

    if tag:
        message = f"Tagging {total_audios} exported files ...."
        update_notification.update(message=message)
        for audio in audios:
            ExportTag.objects.create(user_id=user_id, tag=tag, audio=audio)

    message = f"Export completed successfully. Exported {total_audios} files, kkipped {skip_count}."
    update_notification.update(message=message)
    Notification.objects.create(
        message=
        f"Exported {total_audios} files successfully. Click on the attached link to download.",
        url=base_url + settings.MEDIA_URL + output_filename,
        title="Data Exported",
        type="success",
        user_id=user_id)


@shared_task()
def convert_files_to_mp3(audio_status=None):
    audios = Audio.objects.filter(
        main_file_format="wav").filter(Q(file_mp3=None) | Q(
            file_mp3="")).order_by("validation_count")
    if audio_status:
        audios = audios.filter(audio_status=audio_status)
    audios = audios.values("id")

    for item in audios:
        convert_audio_file_to_mp3(item.get("id"))


@shared_task()
def convert_audio_file_to_mp3(audio_id):
    audio = Audio.objects.filter(id=audio_id).first()
    if audio and audio.file_mp3 and os.path.isfile(audio.file_mp3.path):
        return

    input_file = audio.file.path
    if not input_file or ".mp3" in input_file: return

    output_file = input_file.split(".wav")[0] + ".mp3"
    if not output_file: return
    try:
        stream = ffmpeg.input(input_file)
        stream = ffmpeg.output(stream, output_file)
        res = ffmpeg.run(stream, quiet=True, overwrite_output=True)
    except Exception as e:
        logger.error(str(e))
        return

    # Update audio object
    try:
        audio = Audio.objects.filter(id=audio_id).first()
        if not audio or os.path.getsize(output_file) < (1024 * 10): return

        audio.file_mp3 = File(open(output_file, "rb"),
                              output_file.split("/")[-1])
        audio.main_file_format = "mp3"
        if os.path.isfile(output_file):
            os.remove(output_file)
        audio.save()
    except Exception as e:
        logger.error(str(e))


def get_audios_rejected(user):
    from dashboard.models import Audio
    return Audio.objects.filter(submitted_by=user,
                                rejected=True,
                                deleted=False,
                                is_accepted=False).count()


def get_audios_pending(user):
    from dashboard.models import Audio
    return Audio.objects.filter(submitted_by=user,
                                rejected=False,
                                deleted=False,
                                is_accepted=False).count()


def get_audios_accepted(user):
    return Audio.objects.filter(submitted_by=user,
                                rejected=False,
                                deleted=False,
                                is_accepted=True).count()


def get_estimated_deduction_amount(user):
    DEDUCTION_PER_REJECTED = 0.20
    return get_audios_rejected(user) * DEDUCTION_PER_REJECTED


def get_audios_submitted(user):
    from dashboard.models import Audio
    return Audio.objects.filter(deleted=False, submitted_by=user).count()


def get_audios_validated(user):
    from dashboard.models import Audio
    return Audio.objects.filter(validations__user=user).count()


def get_conflicts_resolved(user):
    from dashboard.models import Audio
    return Audio.objects.filter(conflict_resolved_by=user).count()


def get_audios_transcribed(user):
    return Transcription.objects.filter(user=user).count()


def get_transcriptions_resolved(user):
    transcriptions = Transcription.objects.filter(conflict_resolved_by=user)
    try:
        return transcriptions.distinct("audio").count()
    except NotSupportedError as e:
        ## SQLite does not support distanct on files
        return transcriptions.distinct().count()


@shared_task()
def update_user_stats():
    users = User.objects.filter(deleted=False, is_active=True)
    for user in users:
        user.audios_rejected = get_audios_rejected(user)
        user.audios_pending = get_audios_pending(user)
        user.audios_accepted = get_audios_accepted(user)
        user.audios_submitted = get_audios_submitted(user)
        user.audios_validated = get_audios_validated(user)
        user.conflicts_resolved = get_conflicts_resolved(user)
        user.transcriptions_resolved = get_transcriptions_resolved(user)
        user.audios_transcribed = get_audios_transcribed(user)
        user.estimated_deduction_amount = get_estimated_deduction_amount(user)
        user.save()

    # Update leads stats
    lead_ids = User.objects.filter(deleted=False).exclude(
        lead=None).values_list("lead_id", flat=True)
    leads = User.objects.filter(id__in=lead_ids)
    for lead in leads:
        enumerators = User.objects.filter(deleted=False, lead=lead)
        audios = Audio.objects.filter(deleted=False,
                                      submitted_by__in=enumerators)
        total_sumitted = round(
            sum(audios.values_list("duration", flat=True)) / 3600, 2)
        total_approved = round(
            sum(
                audios.filter(audio_status="accepted").values_list(
                    "duration", flat=True)) / 3600, 2)
        total_rejected = round(
            sum(
                audios.filter(audio_status="rejected").values_list(
                    "duration", flat=True)) / 3600, 2)
        User.objects.filter(id=lead.id).update(
            proxy_audios_submitted_in_hours=total_sumitted,
            proxy_audios_rejected_in_hours=total_rejected,
            proxy_audios_accepted_in_hours=total_approved)


@shared_task()
def release_audios_not_being_validated_by_users_assigned():
    configuration = AppConfiguration.objects.first()
    hours_to_keep_audios_for_validation = configuration.hours_to_keep_audios_for_validation if configuration else 6

    expiry_date = datetime.now() - timedelta(
        hours=hours_to_keep_audios_for_validation)
    forgotten_assignments = AudioValidationAssignment.objects.filter(
        created_at__lte=expiry_date)
    deleted, _ = forgotten_assignments.delete()
    logger.info(f"Made {deleted} audios available for reassignment.")


@shared_task()
def release_audios_not_being_transcribed_by_users_assigned():
    configuration = AppConfiguration.objects.first()
    hours_to_keep_audios_for_transcription = configuration.hours_to_keep_audios_for_transcription if configuration else 6

    expiry_date = datetime.now() - timedelta(
        hours=hours_to_keep_audios_for_transcription)
    forgotten_assignments = AudioTranscriptionAssignment.objects.filter(
        created_at__lte=expiry_date)
    deleted, _ = forgotten_assignments.delete()
    logger.info(f"Made {deleted} audios available for reassignment.")


@shared_task()
def clear_temp_dir():
    temp = os.path.join(settings.MEDIA_ROOT, "temps")
    if not os.path.exists(temp):
        os.makedirs(temp)

    for file_name in os.listdir(temp):
        # construct full file path
        file = temp + "/" + file_name
        if os.path.isfile(file):
            logger.info('Deleting file:', file)
            os.remove(file)
