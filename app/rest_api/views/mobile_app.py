import json
import logging
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from setup.models import AppConfiguration
from dashboard.models import Participant, Audio, Image

from rest_api.serializers import (MobileAppConfigurationSerializer,
                                  ImageSerializer, ParticipantSerializer,
                                  UserSerializer)

logger = logging.getLogger("app")


class MyProfile(generics.GenericAPIView):
    """
    Returns the profile of the logged in user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        data = self.serializer_class(user).data
        return Response({"user": data})


class CreateParticipantAPI(generics.GenericAPIView):
    """
    Create a new Participant and return the Participant.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ParticipantSerializer

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()
        serializer = self.get_serializer(data=request_data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            for field in list(e.detail):
                error_message = e.detail.get(field)[0]
                field = field if field != "non_field_errors" else ""
                response_data = {
                    "error_message": f"{field}: {error_message}",
                    "participant": None,
                }
                return Response(response_data, status=status.HTTP_200_OK)
        participant = serializer.save()
        response_data = {
            "error_message": None,
            "participant": self.serializer_class(participant).data,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class MobileAppConfigurationAPI(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = MobileAppConfigurationSerializer

    def get(self, request, *args, **kwargs):
        data = self.serializer_class(AppConfiguration.objects.first(),
                                     context={
                                         "request": request
                                     }).data
        return Response({"configuration": data})


class GetAssignedImagesAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get(self, request, *args, **kwargs):
        batch_number = request.user.assigned_image_batch
        images = Image.objects.filter(is_accepted=True,
                                      batch_number=batch_number)
        data = self.serializer_class(images,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"images": data})


class UploadAudioAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("audio_file")
        audio_data = request.data.get("audio_data")
        participant_data = request.data.get("participant_data")
        audio_data = json.loads(audio_data)
        participant_data = json.loads(participant_data)

        image_id = audio_data.get("remoteImageID", -1)
        image_object = Image.objects.filter(id=image_id).first()
        image_object = image_object or Image.objects.first()
        amount_per_audio = AppConfiguration.objects.first().amount_per_audio

        try:
            if image_id and image_object and file and audio_data and participant_data:
                participant_object = Participant.objects.create(
                    momo_number=participant_data.get("momoNumber"),
                    network=participant_data.get("network"),
                    fullname=participant_data.get("fullname"),
                    gender=participant_data.get("gender"),
                    submitted_by=request.user,
                    age=participant_data.get("age"),
                    amount=amount_per_audio,
                )

                Audio.objects.create(
                    image=image_object,
                    submitted_by=request.user,
                    file=file,
                    duration=audio_data.get("duration"),
                    locale=request.user.locale,
                    device_id=participant_data.get("deviceId"),
                    environment=participant_data.get("environment"),
                    participant=participant_object,
                )
                return Response({
                    "success": True,
                    "message": "Audio uploaded successfully"
                })
        except Exception as e:
            logger.error(e)
        return Response({"success": False, "message": "Error uploading audio"})
