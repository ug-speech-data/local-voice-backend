from django.contrib import admin
from django_celery_beat.models import IntervalSchedule, PeriodicTask

# Register your models here.
from . import tasks
