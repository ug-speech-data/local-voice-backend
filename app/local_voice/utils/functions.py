import datetime
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.html import strip_tags

logger = logging.getLogger("app")


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
    permissions = user.user_permissions.all()
    return [permission.codename for permission in permissions]


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
            "category",
            "audio",
            "image",
            "group",
            "participant",
            "notification",
            "transaction",
            "transcription",
            "validation",
            "group",
            "appconfiguration",
    ]:
        if item in models:
            models.remove(item)

    permissions = Permission.objects.filter(
        content_type__app_label__in=apps_list,
        content_type__model__in=models).order_by("name")
    return permissions
