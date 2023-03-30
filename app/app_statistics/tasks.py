import logging
import datetime

from celery import shared_task
from django.db import NotSupportedError
from django.db.models import Count
from django.db.utils import ProgrammingError
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from dashboard.models import Audio, Image, Transcription, Participant
from local_voice.utils.constants import ParticipantType, ValidationStatus
from setup.models import AppConfiguration

from .models import Statistics

# yapf: disable

logger = logging.getLogger("app")


try:
    PeriodicTask.objects.all().delete()
    schedule, created = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.MINUTES,
    )
    res = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name='Update Statistics',
        task='app_statistics.tasks.update_statistics',
    )

    name = "delete_audios_with_zero_duration"
    schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
    )
    res = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name=name,
        task=f'app_statistics.tasks.{name}',
    )

    name = "release_audios_in_review_for_more_than_ten_minutes"
    schedule, created = IntervalSchedule.objects.get_or_create(every=6,period=IntervalSchedule.MINUTES)
    res = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name=name,
        task=f"app_statistics.tasks.{name}")

    name = "convert_files_to_mp3"
    schedule, created = IntervalSchedule.objects.get_or_create(every=30,period=IntervalSchedule.MINUTES)
    res = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name=name,
        task=f"rest_api.tasks.{name}")

    name = "update_user_stats"
    schedule, created = IntervalSchedule.objects.get_or_create(every=30,period=IntervalSchedule.MINUTES)
    res = PeriodicTask.objects.get_or_create(
        interval=schedule,
        name=name,
        task=f"rest_api.tasks.{name}")
except ProgrammingError:
    pass

@shared_task()
def delete_audios_with_zero_duration():
    configuration = AppConfiguration.objects.first()
    audios = Audio.objects.filter(duration=0)
    deleted = audios.delete()

    if deleted:
        # Update payment
        for part in Participant.objects.filter(paid=False):
            if part.type == ParticipantType.INDEPENDENT.value:
                amount = configuration.individual_audio_aggregators_amount_per_audio if configuration else 0
            elif part.type == ParticipantType.ASSISTED.value:
                amount = configuration.participant_amount_per_audio if configuration else 0
            part.update_amount(amount)

def language_statistics_in_hours(lang,locale):
    hours_in_seconds = 3600
    decimal_places = 2
    audios = Audio.objects.filter(deleted=False, locale=locale)
    transcriptions = Transcription.objects.filter(deleted=False, audio__locale=locale)

    submitted = round(sum([audio.duration for audio in audios]) / hours_in_seconds,decimal_places)
    single_validation = round(sum([audio.duration for audio in audios.annotate(vals_count=Count("validations")).filter(vals_count=1)]) / hours_in_seconds,decimal_places)
    double_validation = round(sum([audio.duration for audio in audios.annotate(vals_count=Count("validations")).filter(vals_count__gt=1)]) / hours_in_seconds,decimal_places)
    conflicts = round(sum([audio.duration for audio in audios.annotate(vals_count=Count("validations")).filter(rejected=False, is_accepted=False, vals_count__gt=1)]) / hours_in_seconds,decimal_places)
    approved = round(sum([audio.duration for audio in audios.filter(is_accepted=True, rejected=False)]) / hours_in_seconds,decimal_places)

    unique_transcriptions = transcriptions
    try:
        if unique_transcriptions.distinct("audio").exists():
            unique_transcriptions = unique_transcriptions.distinct("audio")
    except NotSupportedError as e:
        # Sqlite Deos not support distinct operation on columns
        logger.error(str(e))
    audios_transcribed_hours = round(sum([transcription.audio.duration for transcription in unique_transcriptions]) / hours_in_seconds, decimal_places)

    return {
        f"{lang}_audios_submitted_in_hours": submitted,
        f"{lang}_audios_single_validation_in_hours": single_validation,
        f"{lang}_audios_double_validation_in_hours": double_validation,
        f"{lang}_audios_validation_conflict_in_hours": conflicts,
        f"{lang}_audios_approved_in_hours": approved,
        f"{lang}_audios_transcribed_in_hours": audios_transcribed_hours,
    }

def language_statistics(lang,locale):
    audios = Audio.objects.filter(deleted=False, locale=locale)
    transcriptions = Transcription.objects.filter(deleted=False, audio__locale=locale)
    submitted = audios.count()

    single_validation = audios.annotate(vals_count=Count("validations")).filter(vals_count=1).count()
    double_validation = audios.annotate(vals_count=Count("validations")).filter(vals_count__gt=1).count()
    conflicts = audios.annotate(vals_count=Count("validations")).filter(rejected=False, is_accepted=False, vals_count__gt=1).count()
    approved = audios.filter(is_accepted=True, rejected=False).count()

    unique_transcriptions = transcriptions
    try:
        if unique_transcriptions.distinct("audio").exists():
            unique_transcriptions = unique_transcriptions.distinct("audio")
    except NotSupportedError as e:
        # Sqlite Deos not support distinct operation on columns
        logger.error(str(e))

    return {
        f"{lang}_audios_submitted": submitted,
        f"{lang}_audios_single_validation": single_validation,
        f"{lang}_audios_double_validation": double_validation,
        f"{lang}_audios_validation_conflict": conflicts,
        f"{lang}_audios_approved": approved,
        f"{lang}_audios_transcribed": unique_transcriptions.count(),
    }


@shared_task()
def update_statistics():
    hours_in_seconds = 3600
    decimal_places = 4
    stats = Statistics.objects.first()
    if not stats:
        stats = Statistics.objects.create()

    audios = Audio.objects.filter(deleted=False)
    images = Image.objects.filter(deleted=False)
    transcriptions = Transcription.objects.filter(deleted=False)

    images_submitted = images.count()
    images_approved = images.filter(is_accepted=True).count()
    stats.images_approved = images_approved
    stats.images_submitted = images_submitted
    stats.save()

    audios_submitted = audios.count()
    audios_approved = audios.filter(is_accepted=True).count()
    audios_transcribed = transcriptions.count()

    stats.audios_submitted = audios_submitted
    stats.audios_approved = audios_approved
    stats.audios_transcribed = audios_transcribed
    stats.save()

    unique_transcriptions = transcriptions
    try:
        if unique_transcriptions.distinct("audio").exists():
            unique_transcriptions = unique_transcriptions.distinct("audio")
    except NotSupportedError as e:
        # Sqlite Deos not support distinct operation on columns
        logger.error(str(e))

    audios_hours_submitted = round(sum([audio.get("duration") for audio in audios.values("duration")]) / hours_in_seconds, decimal_places)
    audios_hours_approved = round(sum([audio.get("duration") for audio in audios.filter(is_accepted=True).values("duration") ]) / hours_in_seconds, decimal_places)
    audios_hours_transcribed = round(sum([transcription.audio.duration for transcription in unique_transcriptions]) / hours_in_seconds, decimal_places)
    stats.audios_hours_submitted = audios_hours_submitted
    stats.audios_hours_approved = audios_hours_approved
    stats.audios_hours_transcribed = audios_hours_transcribed
    stats.save()

    languages = [("ewe", "ee_gh"), ("akan", "ak_gh"), ("ikposo","kpo_gh"), ("dagaare","dag_gh"), ("dagbani", "dga_gh")]
    for lang, locale in languages:
        language_stat = language_statistics(lang,locale)
        setattr(stats,f"{lang}_audios_submitted",language_stat.get(f"{lang}_audios_submitted"))
        setattr(stats,f"{lang}_audios_single_validation",language_stat.get(f"{lang}_audios_single_validation"))
        setattr(stats,f"{lang}_audios_double_validation",language_stat.get(f"{lang}_audios_double_validation"))
        setattr(stats,f"{lang}_audios_validation_conflict",language_stat.get(f"{lang}_audios_validation_conflict"))
        setattr(stats,f"{lang}_audios_approved",language_stat.get(f"{lang}_audios_approved"))
        setattr(stats,f"{lang}_audios_transcribed",language_stat.get(f"{lang}_audios_transcribed"))

        # Hours
        language_stat_in_hours = language_statistics_in_hours(lang,locale)
        setattr(stats,f"{lang}_audios_submitted_in_hours",language_stat_in_hours.get(f"{lang}_audios_submitted_in_hours"))
        setattr(stats,f"{lang}_audios_single_validation_in_hours",language_stat_in_hours.get(f"{lang}_audios_single_validation_in_hours"))
        setattr(stats,f"{lang}_audios_double_validation_in_hours",language_stat_in_hours.get(f"{lang}_audios_double_validation_in_hours"))
        setattr(stats,f"{lang}_audios_validation_conflict_in_hours",language_stat_in_hours.get(f"{lang}_audios_validation_conflict_in_hours"))
        setattr(stats,f"{lang}_audios_approved_in_hours",language_stat_in_hours.get(f"{lang}_audios_approved_in_hours"))
        setattr(stats,f"{lang}_audios_transcribed_in_hours",language_stat_in_hours.get(f"{lang}_audios_transcribed_in_hours"))
    stats.save()


@shared_task()
def release_audios_in_review_for_more_than_ten_minutes():
    updated_time = datetime.datetime.now() - datetime.timedelta(minutes=5)
    orphan_objects = Audio.objects.filter(updated_at__lte=updated_time, audio_status=ValidationStatus.IN_REVIEW.value)
    res = orphan_objects.update(audio_status=ValidationStatus.PENDING.value)
    return f"Made {res} audios available"
