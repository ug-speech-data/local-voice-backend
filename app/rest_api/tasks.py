import os
import zipfile
from datetime import datetime

import pandas as pd
from celery import shared_task
from django.conf import settings

from dashboard.models import Audio, Notification


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
        audio_filename = audio.file.name
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
