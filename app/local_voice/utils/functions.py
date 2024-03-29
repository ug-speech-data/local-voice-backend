import datetime
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db.models import Count, Q
from django.utils.html import strip_tags

from local_voice.utils.constants import ValidationStatus

logger = logging.getLogger("app")


def apply_filters(objects, filters):
    if "archive" not in "".join(filters) and hasattr(objects.first(), "archived"):
        objects = objects.filter(archived=False)

    for filter in filters:
        filter = filter.split(":")
        if len(filter) == 2:
            key, value = filter
            if hasattr(objects.first(), key):
                if type(getattr(objects.first(), key)) == bool:
                    value = "1" in value or "t" in value
            if value == "null":
                objects = objects.filter(**{key: None})
            else:
                objects = objects.filter(**{key: value})

        # Special case for validation conflict
        elif len(filter) == 3:
            key, value, annotation = filter
            objects = objects.annotate(c=Count(annotation)).filter(
                c__gt=1).filter(second_audio_status=ValidationStatus.PENDING.value)
    return objects.distinct()


def get_errors_from_form(form):
    errors = []
    for field, er in form.errors.items():
        title = field.title().replace("_", " ")
        errors.append(f"{title}: {strip_tags(er)}<br>")
    return "".join(errors)


def make_model_key_value(obj):
    data = {}
    for field in obj._meta.fields:
        if field.name in obj.__dict__:
            value = obj.__dict__[field.name]
            if isinstance(value, datetime.datetime) or isinstance(
                    value, datetime.date):
                value = value.strftime("%Y-%m-%d")
            data[field.name] = value
    return data


def get_all_user_permissions(user):
    permissions = []
    for perm in user.get_all_permissions():
        permissions.append(perm.split(".")[-1])
    return sorted(permissions)


def available_application_permissions():
    all_permissions = [
        perm['codename']
        for perm in Permission.objects.all().values('codename')
    ]
    all_permissions.sort()
    return all_permissions


def relevant_permission_objects():
    apps_list = set([app.split(".")[0]
                     for app in settings.INSTALLED_APPS] + ["auth"])
    apps_list.remove("knox")
    models = []
    for app in apps_list:
        models += [
            model._meta.model_name
            for _, model in apps.all_models[app].items()
        ]
    models = set(models)
    for item in [
            "otp",
            "activitylog",
            "permission",
            "mobileappconfiguration",
            "sysconfig",
            "configuration",
            "wallet",
            "audio",
            "image",
            "participant",
            "notification",
            "transaction",
            "transcription",
            "intervalschedule",
            "periodictasks",
            "solarschedule",
            "statistics",
            "crontabschedule",
            "clockedschedule",
            "periodictask",
            "activitylog",
            "validation",
            "appconfiguration",
    ]:
        if item in models:
            models.remove(item)

    permissions = Permission.objects.filter(
        content_type__app_label__in=apps_list,
        content_type__model__in=models).exclude(codename="manage_payment")\
        .order_by("name")
    return permissions
