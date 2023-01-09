from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response

from accounts.forms import GroupForm, UserForm
from accounts.models import User
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
import pandas as pd
from django.conf import settings
import os
import zipfile

import logging

logger = logging.getLogger("app")


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
        enumerators_group_name = request.data.get("enumerators_group_name")
        enumerators_group = Group.objects.filter(
            name=enumerators_group_name).first()
        configuration = AppConfiguration.objects.first()
        try:
            for key, value in request.data.items():
                if not value: continue
                if hasattr(configuration, key):
                    setattr(configuration, key, value)
            configuration.enumerators_group = enumerators_group
            configuration.save()
        except Exception as e:
            return Response(
                {
                    "error_message": str(e),
                    "message": "Configuration could not be updated"
                },
                status=400)

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


class CollectedParticipantsAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    change_permissions = ["dashboard.change_participant", "setup.manage_setup"]
    delete_permissions = ["dashboard.delete_participant", "setup.manage_setup"]

    serializer_class = ParticipantSerializer
    model_class = Participant
    response_data_label = "participant"
    response_data_label_plural = "participants"

    def post(self, request, *args, **kwargs):
        object_id = request.data.pop("id") or -1
        selected_obj = self.model_class.objects.filter(id=object_id).first()
        for key, value in request.data.items():
            if hasattr(selected_obj, key):
                setattr(selected_obj, key, value)
        selected_obj.save()

        return Response({
            "message":
            "Participant update successfully",
            self.response_data_label:
            self.serializer_class(selected_obj, context={
                "request": request
            }).data
        })


class ReShuffleImageIntoBatches(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_setup"]

    def post(self, request, *args, **kwargs):
        number_of_batches = AppConfiguration.objects.first().number_of_batches
        for count, image in enumerate(
                Image.objects.filter(is_accepted=True).order_by("id")):
            image.batch_number = count % number_of_batches + 1
            image.save()
        logger.info(
            f"Reshuffle {count + 1} images into {number_of_batches} batches.")
        return Response({
            "message":
            f"Reshuffle {count + 1} images into {number_of_batches} batches."
        })


class AssignImageBatchToUsers(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_setup"]

    def post(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        enumerators_group = configuration.enumerators_group
        number_of_batches = configuration.number_of_batches

        # Reset all assigned image batch
        User.objects.filter(assigned_image_batch__gt=-1).update(
            assigned_image_batch=-1)

        count = -1
        for count, user in enumerate(enumerators_group.user_set.all()):
            user.assigned_image_batch = count % number_of_batches + 1
            user.save()

        return Response({
            "message":
            f"Shuffled {count + 1} users among {number_of_batches} batches."
        })


class WebAppConfigurations(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        config = AppConfiguration.objects.first()
        return Response({
            "message": "Web app configurations",
            "configurations": {
                "android_apk_url":
                request.build_absolute_uri(config.android_apk.url)
                if config.android_apk else "",
            }
        })


class NotificationAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(
            is_read=False, user=request.user).order_by("-created_at")[:3]
        return Response({
            "message":
            "Notifications",
            "notifications":
            NotificationSerializer(notifications, many=True).data
        })


class ExportAudioData(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    permission_classes = [permissions.AllowAny]
    required_permissions = ["setup.manage_setup"]

    def get(self, request, *args, **kwargs):
        # Create temp directory
        temp = os.path.join(settings.MEDIA_ROOT, "temps")
        if not os.path.exists(temp):
            os.makedirs(temp)

        output_filename = 'temps/download.zip'
        output_dir = settings.MEDIA_ROOT / output_filename
        zip_file = zipfile.ZipFile(output_dir, 'w')

        columns = [
            'IMAGE_URL',
            "AUDIO_URL",
            'ORG_NAME',
            'PROJECT_NAME ',
            'SPEAKER_ID',
            "LOCALE",
            "GENDER",
            "AGE",
            "DEVICE",
            "ENVIRONMENT",
            "YEAR",
        ]
        rows = []
        audios = Audio.objects.all()
        for audio in audios:
            if not (audio.file and audio.image and audio.image.file):
                continue

            # Copy audio and image files to temp directory
            audio_filename = audio.file.name
            image_filename = audio.image.file.name
            zip_file.write(settings.MEDIA_ROOT / audio_filename,
                           arcname=audio_filename)
            zip_file.write(settings.MEDIA_ROOT / image_filename,
                           arcname=image_filename)

            row = [
                audio.image.file.url,
                audio.file.url,
                "University of Ghana",
                "Waxal",
                audio.participant.id,
                audio.locale,
                audio.participant.gender,
                audio.participant.age,
                audio.device_id,
                audio.environment,
                audio.year,
            ]
            rows.append(row)

        # Write data to excel file
        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(temp + '/waxal-project-data.xlsx')
        zip_file.write(temp + '/waxal-project-data.xlsx',
                       arcname='waxal-project-data.xlsx')
        zip_file.close()
        os.remove(temp + '/waxal-project-data.xlsx')

        Notification.objects.create(
            message="Data exported successfully",
            url=request.build_absolute_uri(settings.MEDIA_URL +
                                           output_filename),
            title="Data Exported",
            type="success",
            user=request.user)

        return Response({
            "message":
            "Data exported successfully",
            "url":
            request.build_absolute_uri(settings.MEDIA_URL + output_filename)
        })
