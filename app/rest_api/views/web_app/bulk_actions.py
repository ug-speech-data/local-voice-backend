import logging

from rest_framework import generics, permissions
from rest_framework.response import Response

from dashboard.models import Audio, Image, Participant, Transcription
from local_voice.utils.constants import ValidationStatus
from rest_api.permissions import APILevelPermissionCheck

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
    required_permissions = []

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        images = Image.objects.filter(id__in=ids)
        counts = images.count()

        if action == "approve":
            images.update(is_accepted=True)
            return Response({"message": f"Approved {counts} images."})

        if action == "reject":
            images.update(is_accepted=False)
            return Response({"message": f"Rejected {counts} images."})

        if action == "delete":
            images.delete()
            return Response({"message": f"Deleted {counts} images."})
        return Response({"message": "Invalid operation"})


class AudiosBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") or []
        action = request.data.get("action")

        audios = Audio.objects.filter(id__in=ids, deleted=False)

        if action != "delete":
            is_accepted = action == "approve"
            rejected = not is_accepted
            status = ValidationStatus.ACCEPTED.value if is_accepted else ValidationStatus.REJECTED
            for audio in audios:
                Audio.objects.filter(id=audio.id).update(
                    second_audio_status=status)
                if not audio.conflict_resolved_by:
                    Audio.objects.filter(id=audio.id).update(
                        conflict_resolved_by=request.user)
            return Response({"message": f"Updated {audios.count()} audios."})

        elif action == "delete":
            res, _ = audios.update(deleted=True)
            return Response({"message": f"Deleted {res} audios."})
        return Response({"message": "Invalid operation"})


class TranscriptionsBulkAction(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = []

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
