from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response

from accounts.forms import GroupForm, UserForm
from accounts.models import User
from rest_api.tasks import export_audio_data
from rest_api.serializers import AudioSerializer, TranscriptionSerializer, ParticipantSerializer, NotificationSerializer
from dashboard.forms import CategoryForm
from dashboard.models import Category, Image, Audio, Transcription, Participant, Notification
from local_voice.utils.functions import (get_errors_from_form,
                                         relevant_permission_objects)
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (AppConfigurationSerializer,
                                  CategorySerializer,
                                  GroupPermissionSerializer, GroupSerializer,
                                  ImageSerializer, UserSerializer)
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration

import logging

logger = logging.getLogger("app")


class ParticipantsBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        participants = Participant.objects.filter(id__in=ids)

        if action == "pay":
            for participant in participants:
                participant.pay_participant(request.user)
            return Response({
                "message":
                f"Payment request successfully submitted for {participants.count()} participants."
            })

        if action == "payment_status_check":
            for participant in participants:
                participant.check_payment_status()

        return Response({
            "message":
            f"Checking payment status of {participants.count()} participants."
        })


class ImagesBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        images = Image.objects.filter(id__in=ids)

        if action == "approve":
            images.update(is_accepted=True)
            return Response({"message": f"Approved {images.count()} images."})

        if action == "reject":
            images.update(is_accepted=False)

        return Response({"message": f"Rejected {images.count()} images."})


class AudiosBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        audios = Audio.objects.filter(id__in=ids)

        if action == "approve":
            audios.update(is_accepted=True)
            return Response({"message": f"Approved {audios.count()} audios."})

        if action == "reject":
            audios.update(is_accepted=False)

        return Response({"message": f"Rejected {audios.count()} audios."})


class TranscriptionsBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        transcriptions = Transcription.objects.filter(id__in=ids)

        if action == "approve":
            transcriptions.update(is_accepted=True)
            return Response({
                "message":
                f"Approved {transcriptions.count()} transcriptions."
            })

        if action == "reject":
            transcriptions.update(is_accepted=False)

        return Response(
            {"message": f"Rejected {transcriptions.count()} transcriptions."})
