import logging
from importlib import import_module
import time

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.cache import cache

from accounts.models import ActivityLog

logger = logging.getLogger("user_activity")


class UserRestrict(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Checks if different session exists for user and deletes it.
        """
        if request.user.is_authenticated:
            cache_timeout = 86400
            cache_key = "user_pk_%s_restrict" % request.user.pk
            cache_value = cache.get(cache_key)

            if cache_value:
                if request.session.session_key != cache_value:
                    engine = import_module(settings.SESSION_ENGINE)
                    session = engine.SessionStore(session_key=cache_value)
                    session.delete()
                    cache.set(cache_key, request.session.session_key,
                              cache_timeout)
            else:
                cache.set(cache_key, request.session.session_key,
                          cache_timeout)
        return self.get_response(request)


class AddPermissionToResponse(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Add user's permission bloom filter to every API request.
        """
        response = self.get_response(request)
        # if request.user.is_authenticated:
        #     if settings.DEBUG and request.user.user_permissions.count() == 0:
        #         for perm in Permission.objects.all():
        #             request.user.user_permissions.add(perm)
        return response


class LogUserVisits(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Log the different pages visited by user.
        """
        start = time.time_ns()
        response = self.get_response(request)

        path = request.path
        ignore = ["assets", "uploads", "static", "admin", "media"]
        if not any(x in path.split("/") for x in ignore):
            if not settings.DEBUG:
                username = request.user.email_address if request.user.is_authenticated else "Anonymous"
                action = "%s %s" % (request.method, path)

                end = time.time_ns()
                duration_in_mills = (end - start) // 1_000_000

                ActivityLog.objects.create(username=username,
                                           action=action,
                                           duration_in_mills=duration_in_mills)
        return response
