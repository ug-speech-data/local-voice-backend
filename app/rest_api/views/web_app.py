from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response

from accounts.forms import GroupForm, UserForm
from accounts.models import User
from rest_api.serializers import AudioSerializer, TranscriptionSerializer
from dashboard.forms import CategoryForm
from dashboard.models import Category, Image, Audio, Transcription
from local_voice.utils.functions import (get_errors_from_form,
                                         relevant_permission_objects)
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (AppConfigurationSerializer,
                                  CategorySerializer,
                                  GroupPermissionSerializer, GroupSerializer,
                                  ImageSerializer, UserSerializer)
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration


class GetImagesToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_image"]
    serializer_class = ImageSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        offset = request.GET.get("offset", -1)
        required_image_validation_count = configuration.required_image_validation_count

        image = Image.objects.filter(
            id__gt=offset,
            is_downloaded=True,
            is_accepted=False,
            validation_count__lt=required_image_validation_count)\
                .exclude(validations__user=request.user) \
            .order_by("id")\
                .first()

        data = self.serializer_class(image, context={
            "request": request
        }).data if image else None
        return Response({
            "image": data,
        })


class ValidateImage(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_image"]

    def post(self, request, *args, **kwargs):
        image_id = request.data.get("image_id")
        status = request.data.get("status")
        category_names = request.data.get("categories")
        image = Image.objects.filter(id=image_id).first()
        if image:
            image.validate(request.user, status, category_names)

        return Response({"message": "Image validated successfully"})


class GetAudiosToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]
    serializer_class = AudioSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        offset = request.GET.get("offset", -1)
        required_audio_validation_count = configuration.required_audio_validation_count

        audio = Audio.objects.filter(
            id__gt=offset,
            is_accepted=False,
            validation_count__lt=required_audio_validation_count)\
                .exclude(validations__user=request.user) \
            .order_by("id")\
                .first()

        data = self.serializer_class(audio, context={
            "request": request
        }).data if audio else None
        return Response({
            "audio": data,
        })


class GetAudiosToTranscribe(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_transcription"]
    serializer_class = AudioSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count
        offset = request.GET.get("offset", -1)

        audio = Audio.objects.filter(
            id__gt=offset,
            is_accepted=True,
            transcription_count__lt=required_transcription_validation_count)\
                .exclude(validations__user=request.user) \
            .order_by("id")\
                .first()

        data = self.serializer_class(audio, context={
            "request": request
        }).data if audio else None
        return Response({
            "audio": data,
        })


class GetTranscriptionToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.transcribe_audio"]
    serializer_class = TranscriptionSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count
        offset = request.GET.get("offset", -1)


        transcription = Transcription.objects.filter(
            id__gt=offset,
            is_accepted=False,
            validation_count__lt=required_transcription_validation_count)\
                .exclude(validations__user=request.user) \
            .order_by("id")\
                .first()

        data = self.serializer_class(transcription,
                                     context={
                                         "request": request
                                     }).data if transcription else None
        return Response({
            "transcription": data,
        })


class ValidateAudio(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]

    def post(self, request, *args, **kwargs):
        audio_id = request.data.get("id")
        status = request.data.get("status")
        audio = Audio.objects.filter(id=audio_id).first()
        if audio:
            audio.validate(request.user, status)
        return Response({"message": "Image validated successfully"})


class SubmitTranscription(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.transcribe_audio"]

    def post(self, request, *args, **kwargs):
        audio_id = request.data.get("id")
        text = request.data.get("text")
        transcription, _ = Transcription.objects.get_or_create(
            audio_id=audio_id, user=request.user)
        transcription.text = text
        transcription.save()
        return Response({"message": "Image validated successfully"})


class ValidateTranscription(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_transcription"]

    def post(self, request, *args, **kwargs):
        transcription_id = request.data.get("id")
        status = request.data.get("status")
        transcription = Transcription.objects.filter(
            id=transcription_id).first()
        if transcription:
            transcription.validate(request.user, status)
        return Response({"message": "Transcription validated successfully"})


class CategoriesAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    add_permissions = ["dashboard.add_category", "setup.manage_setup"]
    change_permissions = ["dashboard.change_category", "setup.manage_setup"]
    delete_permissions = ["dashboard.delete_category", "setup.manage_setup"]

    serializer_class = CategorySerializer
    model_class = Category
    form_class = CategoryForm
    response_data_label = "category"
    response_data_label_plural = "categories"


class GroupsAPI(SimpleCrudMixin):
    """
    Groups API: Create groups to manage users.
    """
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = [
        "auth.add_group", "auth.change_group", "auth.delete_group",
        "auth.view_group", "setup.manage_setup"
    ]
    serializer_class = GroupSerializer
    model_class = Group
    form_class = GroupForm
    response_data_label = "group"
    response_data_label_plural = "groups"


class PermissionsAPI(SimpleCrudMixin):
    """
    Manage group/user permissions.
    """
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_setup"]
    serializer_class = GroupPermissionSerializer
    model_class = Permission

    def get(self, request, group_id, *args, **kwargs):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response({"error_message": "Group not found"}, status=404)
        permissions = relevant_permission_objects()
        data = self.serializer_class(permissions,
                                     context={
                                         "group": group
                                     },
                                     many=True).data
        return Response({"permissions": data})

    def post(self, request, group_id, *args, **kwargs):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response({"error_message": "Group not found"}, status=404)
        permission_ids = request.data.get("permissions", [])
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.set(permissions)
        return Response({"message": "Permissions updated successfully"})


class UsersAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    add_permissions = ["accounts.add_user", "setup.manage_setup"]
    change_permissions = ["accounts.change_user", "setup.manage_setup"]
    delete_permissions = ["accounts.delete_user", "setup.manage_setup"]

    serializer_class = UserSerializer
    model_class = User
    form_class = UserForm
    response_data_label = "user"
    response_data_label_plural = "users"

    def post(self, request, *args, **kwargs):
        obj_id = request.data.get("id")
        new_password = request.data.get("password")
        group_names = request.data.get("groups")
        groups = Group.objects.filter(name__in=group_names)
        obj = None
        if obj_id:
            obj = self.model_class.objects.filter(id=obj_id).first()
        form = self.form_class(request.data, instance=obj)
        if form.is_valid():
            user = form.save()
            if new_password and len(new_password) > 0:
                user.set_password(new_password)
            user.groups.set(groups)
            user.save()
            return Response({
                "message":
                f"{self.model_class.__name__} saved successfully",
                self.response_data_label:
                self.serializer_class(form.instance).data,
            })
        return Response({
            "message": f"{self.model_class.__name__} could not be saved",
            "error_message": get_errors_from_form(form),
        })


class AppConfigurationAPI(generics.GenericAPIView):
    """
    Manage app configuration.
    """
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_setup"]
    serializer_class = AppConfigurationSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        data = self.serializer_class(configuration,
                                     context={
                                         "request": request
                                     }).data
        return Response({"configurations": data})

    def post(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        try:
            for key, value in request.data.items():
                print(key, value, "key value")
                if not value: continue
                if hasattr(configuration, key):
                    setattr(configuration, key, value)
            configuration.save()
        except Exception as e:
            return Response({
                "error_message": str(e),
                "message": "Configuration could not be updated"
            })

        return Response({
            "message":
            "Configuration updated successfully",
            "configurations":
            self.serializer_class(configuration, context={
                "request": request
            }).data
        })


class CollectedImagesAPI(SimpleCrudMixin):
    """
    Get Images API
    """
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    add_permissions = ["dashboard.add_image", "setup.manage_setup"]
    change_permissions = ["dashboard.change_image", "setup.manage_setup"]
    delete_permissions = ["dashboard.delete_image", "setup.manage_setup"]

    serializer_class = ImageSerializer
    model_class = Image
    response_data_label = "image"
    response_data_label_plural = "images"

    def post(self, request, *args, **kwargs):
        image_id = request.data.get("id") or -1
        image_obj = self.model_class.objects.filter(id=image_id).first()
        category_names = request.data.pop("categories", None)
        categories = Category.objects.filter(name__in=category_names)
        image_obj.categories.set(categories)
        image_obj.save()
        for key, value in request.data.items():
            if hasattr(image_obj, key):
                setattr(image_obj, key, value)

        if not (image_obj.is_accepted and image_obj.is_downloaded):
            image_obj.validations.clear()
            image_obj.categories.clear()
        image_obj.save()

        return Response({
            "message":
            "Image updated successfully",
            self.response_data_label:
            self.serializer_class(image_obj, context={
                "request": request
            }).data
        })


class CollectedAudiosAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    add_permissions = ["dashboard.add_audio", "setup.manage_setup"]
    change_permissions = ["dashboard.change_audio", "setup.manage_setup"]
    delete_permissions = ["dashboard.delete_audio", "setup.manage_setup"]

    serializer_class = AudioSerializer
    model_class = Audio
    response_data_label = "audio"
    response_data_label_plural = "audios"

    def post(self, request, *args, **kwargs):
        object_id = request.data.pop("id") or -1
        image_obj = self.model_class.objects.filter(id=object_id).first()
        for key, value in request.data.items():
            if hasattr(image_obj, key):
                setattr(image_obj, key, value)

        if not image_obj.is_accepted:
            image_obj.validations.clear()
        image_obj.save()

        return Response({
            "message":
            "Audio update successfully",
            self.response_data_label:
            self.serializer_class(image_obj, context={
                "request": request
            }).data
        })


class CollectedTranscriptionsAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    change_permissions = [
        "dashboard.change_transcription", "setup.manage_setup"
    ]
    delete_permissions = [
        "dashboard.delete_transcription", "setup.manage_setup"
    ]

    serializer_class = TranscriptionSerializer
    model_class = Transcription
    response_data_label = "transcription"
    response_data_label_plural = "transcriptions"

    def post(self, request, *args, **kwargs):
        object_id = request.data.pop("id") or -1
        selected_obj = self.model_class.objects.filter(id=object_id).first()
        for key, value in request.data.items():
            if hasattr(selected_obj, key):
                setattr(selected_obj, key, value)

        if not selected_obj.is_accepted:
            selected_obj.validations.clear()
        selected_obj.save()

        return Response({
            "message":
            "Transcription update successfully",
            self.response_data_label:
            self.serializer_class(selected_obj, context={
                "request": request
            }).data
        })
