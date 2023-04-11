import os
import logging
import zipfile
from datetime import datetime
import ffmpeg
from django.db.models import Q

import pandas as pd
from celery import shared_task
from django.conf import settings
from django.core.files import File
from accounts.models import User

from dashboard.models import Audio, Notification

logger = logging.getLogger("app")


@shared_task()
def export_audio_data(user_id, data, base_url):
    # Create temp directory
    temp = os.path.join(settings.MEDIA_ROOT, "temps")
    if not os.path.exists(temp):
        os.makedirs(temp)

    timestamp = str(datetime.today()).split(".")[0]
    output_filename = f"temps/export_audio_{timestamp}.zip"
    output_dir = settings.MEDIA_ROOT / output_filename
    zip_file = zipfile.ZipFile(output_dir, 'w')

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
    audios = Audio.objects.filter(is_accepted=True)
    for audio in audios:
        if not (audio.file and audio.image and audio.image.file):
            continue

        # Copy audio and image files to temp directory
        audio_filename = audio.file_mp3.name if audio.file_mp3 else audio.file.name

        image_filename = audio.image.file.name
        new_image_filename = image_filename.split("/")[0] + "/" + str(
            audio.id).zfill(4) + "." + image_filename.split(".")[-1]
        zip_file.write(settings.MEDIA_ROOT / audio_filename,
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
            participant.gender if participant else audio.submitted_by.gender,
            participant.age if participant else audio.submitted_by.age,
            audio.device_id,
            audio.environment,
            audio.year,
        ]
        rows.append(row)

    # Write data to excel file
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(temp + '/waxal-project-data.xlsx')
    zip_file.write(temp + '/waxal-project-data.xlsx',
                   arcname='waxal-project-data.xlsx')
    zip_file.close()
    os.remove(temp + '/waxal-project-data.xlsx')

    Notification.objects.create(
        message=
        "Data exported successfully. Click on the link below to download.",
        url=base_url + settings.MEDIA_URL + output_filename,
        title="Data Exported",
        type="success",
        user_id=user_id)


@shared_task()
def convert_files_to_mp3(audio_status=None):
    audios = Audio.objects.filter(
        main_file_format="wav").filter(Q(file_mp3=None) | Q(
            file_mp3="")).order_by("validation_count")
    print("audios", audios)
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


@shared_task()
def update_user_stats():
    users = User.objects.all()
    for user in users:
        user.audios_rejected = get_audios_rejected(user)
        user.audios_pending = get_audios_pending(user)
        user.audios_accepted = get_audios_accepted(user)
        user.audios_submitted = get_audios_submitted(user)
        user.audios_validated = get_audios_validated(user)
        user.estimated_deduction_amount = get_estimated_deduction_amount(user)
        user.save()
