from redis.exceptions import ConnectionError
import redis
from datetime import timedelta
import logging
import time
from importlib import import_module

from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response

from accounts.models import ActivityLog

logger = logging.getLogger("user_activity")


redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class UserRestrict(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Checks if different session exists for user and deletes it.
        """
        print("cache_key","cache_key")

        if request.user.is_authenticated:
            cache_timeout = 86400
            cache_key = "user_pk_%s_restrict" % request.user.pk
            cache_value = cache.get(cache_key)

            print("cache_key",cache_key)

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


class RateLimitter(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Log the different pages visited by user.
        """
        print("request.user",request.user)
        if request.user.is_authenticated:
            user_key = "user_"+request.user.id
        else:
            if not request.session.session_key:
                request.session.create()
            user_key = request.session.session_key

        start = time.time_ns()
        last_visit = None
        try:
            last_visit = redis_client.get(user_key)
            print("last_visit",user_key, last_visit)
        except ConnectionError as e:
            logger.warning("Redis is not working")
            logger.error(str(e))
        if last_visit == None:
            try:
                redis_client.set(user_key, start, ex=timedelta(seconds=20))
            except ConnectionError as e:
                logger.error(str(e))
        else:
            print("exceeded")
            return Response({"message": "Rate limit exceeded"}, 400)

        response = self.get_response(request)

        return response
