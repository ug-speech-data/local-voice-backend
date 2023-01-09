import pandas as pd
from django.conf import settings
import os
import zipfile


def export_data(context):
    # Create temp directory
    temp = os.path.join(settings.MEDIA_ROOT, "temps")
    output_filename = settings.MEDIA_ROOT / 'temps/download.zip'
    zip_file = zipfile.ZipFile(output_filename, 'w')

    if not os.path.exists(temp):
        os.makedirs(temp)

    columns = [
        'IMAGE_URL', "AUDIO_URL", 'ORG_NAME', 'PROJECT_NAME ', 'SPEAKER_ID',
        "LOCALE", "GENDER", "AGE", "DEVICE", "ENVIRONMENT", "YEAR"
    ]
    rows = []
    audios = Audio.objects.all()
    for audio in audios:
        if not (audio.file and audio.image and audio.image.file):
            continue

        # Copy audio and image files to temp directory
        audio_filename = audio.file.name
        image_filename = audio.image.file.name
        zip_file.write(settings.MEDIA_ROOT / audio_filename,
                       arcname=audio_filename)
        zip_file.write(settings.MEDIA_ROOT / image_filename,
                       arcname=image_filename)

        row = [
            audio.image.file.url,
            audio.file.url,
            "University of Ghana",
            "Waxal",
            audio.participant.id,
            audio.locale,
            audio.participant.gender,
            audio.participant.age,
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

    return Response({
        "message":
        "Data exported successfully",
        "url":
        request.build_absolute_uri(settings.MEDIA_URL + 'temps/download.zip')
    })
