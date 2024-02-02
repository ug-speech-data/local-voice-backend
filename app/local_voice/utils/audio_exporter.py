"""Export audio files into drop box."""

import os
import casefy
import dropbox
import threading
import pandas as pd
from typing import List
from django.conf import settings
from django.db.models import Count
from dashboard.models import Audio
from local_voice.utils.constants import TranscriptionStatus

class DropBoxExport:
    def __init__(self, system_id:str, key:str) -> None:
        self.dbx = dropbox.Dropbox(key)
        self.system_id = system_id
    def _preprocess_transcription(self, text:str)->str:
        text = text.strip(".").replace("  ", " ")
        text = casefy.sentencecase(text)
        text += "."
        return text
    def _get_lang_from_locale(self, locale):
        if "ee_gh" in locale:
            return "ewe"
        elif "ak_gh" in locale:
            return "akan"
        elif "dag_gh" in locale:
            return "dagaare"
        elif "dga_gh" in locale:
            return "dagbani"
        elif "kpo_gh" in locale:
            return "ikposo"
    def _upload(self, file_name: str, new_relative_path_name: str | None = None):
        if not new_relative_path_name:
            new_relative_path_name = file_name
        with open(file_name, "rb") as f:
            data = f.read()
            self.dbx.files_upload(data, new_relative_path_name)
    def _export_and_upload_excel(self, lang, audios: List[Audio]):
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
        working_dir = f"/{lang}/batch_10_transcribed"
        for index, audio in enumerate(audios, 1):
            try:
                participant = audio.participant
                transcriptions = "\n\n".join(audio.get_transcriptions())
                transcriptions = self._preprocess_transcription(transcriptions)
                image_ext = audio.image.name.split(".")[-1]
                ext = audio.main_file_format
                row = [
                    f"/{lang}/images/image_{audio.image.image_id}.{image_ext}",
                    audio.image.source_url,
                    f"{working_dir}/audios/audio_{self.system_id}{audio.id}_image_{audio.image.image_id}.{ext}",
                    "University of Ghana",
                    "Waxal",
                    f"{self.system_id}" + str(participant.id if participant else audio.submitted_by.id),
                    audio.locale,
                    transcriptions,
                    participant.gender if participant else audio.submitted_by.gender,
                    participant.age if participant else audio.submitted_by.age,
                    audio.device_id,
                    audio.environment,
                    audio.year,
                ]
                rows.append(row)
            except Exception as e:
                print("ERRRO:", str(e), audio)
            print(f"\n{working_dir}: {index}/{total}", f"{int(index/total*100)}%")
        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(temp + '/transcriptions.xlsx')
        working_dir = f"/{lang}/batch_10_transcribed"
        self._upload(temp + '/transcriptions.xlsx',
                     f"{working_dir}/transcriptions.xlsx")
    def _upload_audios(self, working_dir, audios: List[Audio]):
        total = audios.count()
        for index, audio in enumerate(audios, 1):
            try:
                audio_filename = audio.file_mp3.name if audio.file_mp3 else audio.file.name
                ext = audio.main_file_format
                audio_file_to_upload = settings.MEDIA_ROOT / audio_filename
                audio_destination_path_name = f"{working_dir}/audio_{self.system_id}{audio.id}_image_{audio.image.image_id}.{ext}"
                # Upload audio
                self._upload(audio_file_to_upload, audio_destination_path_name)
            except Exception as e:
                print("ERRRO:", str(e), audio_file_to_upload)
            print(f"\n{working_dir}: {index}/{total}", f"{int(index/total*100)}%")
    def upload_transcriptions(self, locale: str, only_audios=False, only_texts=False, last_id=-1):
        lang = self._get_lang_from_locale(locale)
        audios = Audio.objects.filter(locale=locale, id__gt=last_id)
        audios = audios.filter(second_audio_status="accepted")
        audios = audios.annotate(t_count=Count(
            "transcriptions")).filter(t_count__gt=0)
        audios = audios.filter(
            transcription_status=TranscriptionStatus.ACCEPTED.value)
        audios = audios.order_by("id")
        working_dir = f"/{lang}/batch_10_transcribed/audios"
        if not only_texts:
            self._upload_audios(working_dir, audios)
        if not only_audios:
            self._export_and_upload_excel(lang, audios)
    def upload_audios(self, locale: str, from_batch:int=0, end_batch:int=9, last_id=-1):
        if from_batch < 1 or end_batch > 9:
            print("invalid batch")
            return
        lang = self._get_lang_from_locale(locale)
        audios = Audio.objects.filter(locale=locale, id__gt=last_id)
        audios = audios.filter(second_audio_status="accepted")
        audios = audios.exclude(
            transcription_status=TranscriptionStatus.ACCEPTED.value)
        audios = audios.order_by("id")
        total = audios.count()
        batch_size = total // 9
        threads = []
        for i in range(from_batch-1, end_batch):
            working_dir = f"/{lang}/batch_{i+1}"
            batch_audios = audios[batch_size*i:batch_size*i+batch_size]
            threads.append(threading.Thread(target=self._upload_audios, args=(working_dir, batch_audios), daemon=True))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
