from django.contrib.auth import authenticate, logout
from knox.models import AuthToken
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from rest_api.models import MobileAppConfiguration
from rest_api.serializers import (LoginSerializer,
                                  MobileAppConfigurationSerializer,
                                  ParticipantSerializer, RegisterSerializer,
                                  UserSerializer)


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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MobileAppConfigurationSerializer

    def get(self, request, *args, **kwargs):
        return Response({
            "configuration": {
                "id":
                1,
                "demo_video_url":
                "https://localvoice.pythonanywhere.com/assets/sample-mp4-file-small.mp4"
            }
        })
        data = self.serializer_class(MobileAppConfiguration.objects.first(),
                                     context={
                                         "request": request
                                     }).data
        return Response({"configuration": data})


class GetAssignedImagesAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MobileAppConfigurationSerializer

    def get(self, request, *args, **kwargs):
        return Response({
            "images": [
                {
                    "id":
                    6,
                    "name":
                    "image6",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
                {
                    "id":
                    1,
                    "name":
                    "image1",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
                {
                    "id":
                    2,
                    "name":
                    "image2",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
                {
                    "id":
                    3,
                    "name":
                    "image3",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
                {
                    "id":
                    4,
                    "name":
                    "image4",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
                {
                    "id":
                    5,
                    "name":
                    "image5",
                    "image_url":
                    "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                },
            ]
        })
        data = self.serializer_class(MobileAppConfiguration.objects.first(),
                                     context={
                                         "request": request
                                     }).data
        return Response({"configuration": data})


class UploadAudioAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # serializer_class = MobileAppConfigurationSerializer

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("audio_file")
        remote_image_id = request.POST.get("remote_image_id")
        print(file, remote_image_id)

        return Response({
            "success": True,
            "message": "Audio uploaded successfully"
        })
        # data = self.serializer_class(MobileAppConfiguration.objects.first(),
        #                              context={
        #                                  "request": request
        #                              }).data
        # return Response({"configuration": data})