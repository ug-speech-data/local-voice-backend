from django.contrib.auth import authenticate, logout
from knox.models import AuthToken
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from local_voice.utils.functions import get_all_user_permissions
from rest_api.serializers import (LoginSerializer, RegisterSerializer,
                                  UserSerializer)


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
        user.save()

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

    def get(self, request, *args, **kwargs):
        user = request.user
        data = self.serializer_class(user).data
        return Response({"user": data})


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
        from time import sleep
        sleep(1)
        response_data = {
            "user_permissions": get_all_user_permissions(request.user)
        }
        return Response(response_data, status=status.HTTP_200_OK)
