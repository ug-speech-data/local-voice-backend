import logging

from django.contrib.auth import authenticate, logout
from django.db.models import Count, Q
from knox.models import AuthToken
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.forms import UserForm
from accounts.models import User
from dashboard.models import Audio
from local_voice.utils.constants import ValidationStatus
from local_voice.utils.functions import get_all_user_permissions
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (AudioSerializer, LoginSerializer,
                                  RegisterSerializer, UserSerializer)
from setup.models import AppConfiguration

logger = logging.getLogger("app")


class UserRegistrationAPI(generics.GenericAPIView):
    """
    Register a new user and return a token for the user.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()
        serializer = self.get_serializer(data=request_data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            for field in list(e.detail):
                error_message = e.detail.get(field)[0]
                response_data = {
                    "error_message": f"{field}: {error_message}",
                    "user": None,
                    "token": None,
                }
                return Response(response_data, status=status.HTTP_200_OK)
        user = serializer.save()
        AuthToken.objects.filter(user=user).delete()

        response_data = {
            "error_message": None,
            "user": UserSerializer(user).data,
            "token": AuthToken.objects.create(user)[1],
            "user_permissions": get_all_user_permissions(user)
        }
        return Response(response_data, status=status.HTTP_200_OK)


class UserChangePassword(generics.GenericAPIView):
    """
    Change the password of a user and return a token for the user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        user = authenticate(request,
                            email_address=request.user.email_address,
                            password=old_password)
        if user:
            user.set_password(new_password)
            user.save()
            AuthToken.objects.filter(user=user).delete()

            response_data = {
                "error_message": None,
                "user": UserSerializer(user).data,
                "token": AuthToken.objects.create(user)[1],
            }
            return Response(response_data, status=status.HTTP_200_OK)

        else:
            response_data = {
                "error_message": "Invalid old password",
                "user": None,
                "token": None,
            }
            return Response(response_data, status=status.HTTP_200_OK)


class UserLoginAPI(generics.GenericAPIView):
    """
    Login a user and return a token for the user.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            for field in list(e.detail):
                error_message = e.detail.get(field)[0]
                field = field if field != "non_field_errors" else ""
                response_data = {
                    "error_message": f"{field}: {error_message}",
                    "user": None,
                    "token": None,
                }
                return Response(response_data, status=status.HTTP_200_OK)

        user = serializer.validated_data
        device_id = request.data.get("device_id", "").upper()
        device_ids = user.device_ids.split(",") if user.device_ids else []

        # if device_ids and device_id and device_id not in device_ids:
        #     return Response({
        #         "error_message":
        #         "Sorry, you cannot log in on a different device. Kindly login on your previous device.",
        #         "user": None,
        #         "token": None,
        #     })
        # else:
        device_ids.append(device_id)
        device_ids = set(device_ids)
        user.device_ids = ",".join(device_ids)
        user.save()
        AuthToken.objects.filter(user=user).delete()

        response_data = {
            "error_message": None,
            "user": UserSerializer(user).data,
            "token": AuthToken.objects.create(user)[1],
            "user_permissions": get_all_user_permissions(user)
        }
        return Response(response_data, status=status.HTTP_200_OK)


class UserLogoutAPI(generics.GenericAPIView):
    """
    Logout a user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({"success": True}, status=status.HTTP_200_OK)


class MyProfile(generics.GenericAPIView):
    """
    Returns the profile of the logged in user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    model_class = User
    form_class = UserForm
    response_data_label = "user"
    response_data_label_plural = "users"

    def get(self, request, *args, **kwargs):
        user = request.user
        data = self.serializer_class(user).data
        return Response({self.response_data_label: data})

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()
        password = request_data.pop("password", None)
        old_password = request_data.pop("old_password", None)
        accepted_privacy_policy = request_data.get("accepted_privacy_policy")
        user = request.user
        try:
            for key, value in request_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.accepted_privacy_policy = accepted_privacy_policy == "true"
            user.save()

            # Change password if password is available
            if password:
                if user.check_password(old_password):
                    user.set_password(password)
                else:
                    return Response({"message": f"Invalid old password."})
            user.save()

            return Response({
                "message":
                f"{self.model_class.__name__} saved successfully",
                self.response_data_label:
                self.serializer_class(user).data,
            })
        except Exception as e:
            logger.error(str(e))

            return Response(
                {
                    "message":
                    f"{self.model_class.__name__} could not be saved",
                    "error_message": str(e),
                }, 400)


class LogoutApiView(generics.GenericAPIView):
    """Logout user from all devices."""

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            AuthToken.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out successfully"})


class MyPermissions(generics.GenericAPIView):
    """
    Returns the permission of the logged in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response_data = {
            "user_permissions": get_all_user_permissions(request.user)
        }
        return Response(response_data, status=status.HTTP_200_OK)


class GetAudiosToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]
    serializer_class = AudioSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        offset = request.GET.get("offset", -1)
        required_audio_validation_count = configuration.required_audio_validation_count if configuration else 0

        audios = Audio.objects.annotate(vals_count = Count("validations")).filter(
            deleted=False,
           is_accepted=False,
           rejected=False,
           assignments=None,
           audio_status = ValidationStatus.PENDING.value,
            vals_count__lt=required_audio_validation_count)\
                .exclude(Q(validations__user=request.user)|Q(submitted_by=request.user) | Q(id=offset)) \
            .order_by("-vals_count", "image", "id")

        if not request.user.is_superuser:
            audios = audios.filter(locale=request.user.locale)

        audio = audios.first()
        if audio:
            audio.audio_status = ValidationStatus.IN_REVIEW.value
            audio.save()

        data = self.serializer_class(audio, context={
            "request": request
        }).data if audio else None
        return Response({
            "audio": data,
        })


class ValidateAudio(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]

    def post(self, request, *args, **kwargs):
        audio_id = request.data.get("id")
        status = request.data.get("status")
        configuration = AppConfiguration.objects.first()
        required_audio_validation_count = configuration.required_audio_validation_count if configuration else 2
        audio = Audio.objects.annotate(vals_count=Count("validations")).filter(
            id=audio_id,
            deleted=False,
            vals_count__lt=required_audio_validation_count,
        ).exclude(
            Q(audio_status=ValidationStatus.ACCEPTED.value)
            | Q(audio_status=ValidationStatus.REJECTED.value)).first()
        if audio:
            audio.validate(request.user, status)
        return Response({
            "message": "Validation recorded.",
            "status": "success",
        })
