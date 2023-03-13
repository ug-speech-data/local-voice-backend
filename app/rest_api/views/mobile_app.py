import json
import logging

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from dashboard.models import Image
from rest_api.serializers import (AudioUploadSerializer, ImageSerializer,
                                  MobileAppConfigurationSerializer,
                                  ParticipantSerializer)
from setup.models import AppConfiguration

logger = logging.getLogger("app")


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
        images = Image.objects.filter(is_accepted=True)
        if batch_number > 0:
            images = images.filter(batch_number=batch_number)

        if batch_number != -2:
            images = Image.objects.none()

        data = self.serializer_class(images,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"images": data})


class UploadAudioAPI(generics.GenericAPIView):
    """Upload audio file with the meta data.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AudioUploadSerializer

    def post(self, request, *args, **kwargs):
        # Convert json serialized fields into JSON object
        request_data = {}
        for key, value in request.data.items():
            try:
                request_data[key] = json.loads(value) if type(
                    value) == str else value
            except json.decoder.JSONDecodeError as e:
                # It is not JSON serialization.
                request_data[key] = value

        serializer = self.serializer_class(request.FILES, request_data)
        if serializer.is_valid():
            saved, error = serializer.create(request)
            logger.error(error)
            if saved:
                return Response({
                    "success": True,
                    "message": "Audio uploaded successfully"
                })
            else:
                return Response({"success": False, "message": error}, 400)
        else:
            error_messages = []
            for field, errors in serializer.errors.items():
                error_messages.append(f"{field}: " + str(errors))
            logger.error(error_messages)
            return Response({"error_messages": error_messages}, 400)
