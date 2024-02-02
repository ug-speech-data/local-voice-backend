import dropbox
from django.conf import settings
from dashboard.models import Audio, Image
import pandas as pd
from django.db.models import Count
import os
from dashboard.models import Audio
from local_voice.utils.constants import TranscriptionStatus


dbx = dropbox.Dropbox(settings.DROP_BOX_KEY)
dbx = dropbox.Dropbox('WIepH4NpkxwAAAAAAAAAWRTLjG8MdgsLsd8BHSDVUl0')


def upload(file_name: str, new_relative_path_name: str | None = None):
    if not new_relative_path_name:
        new_relative_path_name = file_name
    with open(file_name, "rb") as f:
        data = f.read()
        dbx.files_upload(data, new_relative_path_name)

audios = Audio.objects.filter(locale="ak_gh")
audios = audios.filter(second_audio_status="accepted")

# Transcription
audios = audios.annotate(t_count=Count("transcriptions")).filter(t_count__gt=0)
audios = audios.filter(transcription_status=TranscriptionStatus.ACCEPTED.value)
audios = audios.order_by("id")

total = audios.count()
chunk_start = 0
for index, audio in enumerate(audios[chunk_start:], chunk_start+1):
    try:
        audio_filename = audio.file_mp3.name if audio.file_mp3 else audio.file.name
        ext = audio.main_file_format
        audio_file_to_upload = settings.MEDIA_ROOT / audio_filename
        working_dir = "/akan/transcribed_audios"
        audio_destination_path_name = f"{working_dir}/audios/audio_a{index}_image_{audio.image.image_id}.{ext}"
        # Upload audio
        upload(audio_file_to_upload, audio_destination_path_name)
    except Exception as e:
        print("ERRRO:", str(e), audio_file_to_upload)
    print(f"{index}/{total}", int(index/total*100))
    # break


# Images
images = Image.objects.filter(is_accepted=True)
total = images.count()
for index, image in enumerate(images, 1):
    try:
        # Upload image
        image_ext = image.name.split(".")[-1]
        image_destination_path_name = f"/akan/images/image_{image.image_id}.{image_ext}"
        image_filename = image.file.name
        image_file_to_upload = settings.MEDIA_ROOT / image_filename
        upload(image_file_to_upload, image_destination_path_name)
    except Exception as e:
        print("ERRRO:", str(e), image_file_to_upload)
    print(f"{index}/{total}", int(index/total*100))
    # break


# Transcriptions
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
    "YEAR"]
rows = list()
temp = os.path.join(settings.MEDIA_ROOT, "temps")
if not os.path.exists(temp):
    os.makedirs(temp)
total = audios.count()
for index, audio in enumerate(audios, 1):
    try:
        participant = audio.participant
        transcriptions = "\n\n".join(audio.get_transcriptions())
        image_ext = audio.image.name.split(".")[-1]
        ext = audio.main_file_format
        row = [
            f"/akan/images/image_{audio.image.image_id}.{image_ext}",
            audio.image.source_url,
            f"/akan/transcribed_audios/audios/audio_a{index}_image_{audio.image.image_id}.{ext}",
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
        print("ERRRO:", str(e), audio)
    print(f"{index}/{total}", int(index/total*100))
df = pd.DataFrame(rows, columns=columns)
df.to_excel(temp + '/transcriptions.xlsx')
print("Uploading")
working_dir = "/akan/transcribed_audios"
upload(temp + '/transcriptions.xlsx', f"{working_dir}/transcriptions2.xlsx")


dur = 0
for audio in audios:
    dur += audio.duration
print(dur / 3600)