import logging

from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import NotSupportedError
from accounts.forms import GroupForm, UserForm
from accounts.models import User
from dashboard.forms import CategoryForm
from dashboard.models import (Audio, Category, Image, Notification,
                              Participant, Transcription)
from local_voice.utils.functions import (apply_filters, get_errors_from_form,
                                         relevant_permission_objects)
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (AppConfigurationSerializer, AudioSerializer,
                                  CategorySerializer,
                                  GroupPermissionSerializer, GroupSerializer,
                                  ImageSerializer, NotificationSerializer,
                                  ParticipantSerializer,
                                  TranscriptionSerializer, UserSerializer)
from rest_api.tasks import export_audio_data
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration

logger = logging.getLogger("app")
from datetime import datetime
from django.utils.timezone import make_aware


class GetImagesToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_image"]
    serializer_class = ImageSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        offset = request.GET.get("offset", -1)
        required_image_validation_count = configuration.required_image_validation_count if configuration else 0
        max_allowed_validation = configuration.max_image_for_validation_per_user if configuration else 0

        start_date = make_aware(datetime.fromisoformat("2023-03-09"))

        # Ensure that the user does not validate to many images
        user_validations = Image.objects.filter(
            validations__is_valid=True,
            validated=False,
            deleted=False,
            created_at__gte=start_date,
            validations__user=request.user).count()
        if user_validations >= max_allowed_validation:
            return Response({
                "image":
                None,
                "message":
                "You have exhausted your permitted number of image validations."
            })

        images = Image.objects.filter(
            id__gt=offset,
            is_downloaded=True,
            deleted=False,
            created_at__gte=start_date,
            is_accepted=False,
            validation_count__lt=required_image_validation_count)\
                .exclude(validations__user=request.user)

        if request.user.assigned_image_batch > -1:  # All images
            images = images.filter(
                batch_number=request.user.assigned_image_batch)

        image = images.first()

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
        image = Image.objects.filter(id=image_id, deleted=False).first()
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
        required_audio_validation_count = configuration.required_audio_validation_count if configuration else 0

        audios = Audio.objects.filter(
            id__gt=offset,
            locale=request.user.locale,
            is_accepted=False,
            validation_count__lt=required_audio_validation_count)\
                .exclude(validations__user=request.user, submitted_by=request.user) \
            .order_by("image", "id")

        # If the user has been assigned a batch of images, they can only validate audios belonging to that batch
        if request.user.assigned_audio_batch >= 0:
            audios = audios.filter(
                image__batch_number=request.user.assigned_audio_batch)

        audio = audios.first()
        data = self.serializer_class(audio, context={
            "request": request
        }).data if audio else None
        return Response({
            "audio": data,
        })


class GetAudiosToTranscribe(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.transcribe_audio"]
    serializer_class = AudioSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else 0
        offset = request.GET.get("offset", -1)

        audio = Audio.objects.filter(
            id__gt=offset,
            is_accepted=True,
            locale=request.user.locale,
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
    required_permissions = ["setup.validate_transcription"]
    serializer_class = TranscriptionSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else None
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
        validators_group_name = request.data.get("validators_group_name")

        enumerators_group = Group.objects.filter(
            name=enumerators_group_name).first()
        validators_group = Group.objects.filter(
            name=validators_group_name).first()
        configuration = AppConfiguration.objects.first()
        if not configuration:
            return Response({"message": "No configurations"}, 400)

        try:
            for key, value in request.data.items():
                if not value: continue
                if hasattr(configuration, key):
                    setattr(configuration, key, value)
            configuration.enumerators_group = enumerators_group
            configuration.validators_group = validators_group
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
        image_obj = self.model_class.objects.filter(id=image_id,
                                                    deleted=False).first()

        if not image_obj:
            return Response({"message": "Invalid image id"}, 400)

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

        if not image_obj:
            return Response({"message": "Invalid image id"}, 400)

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

        if not selected_obj:
            return Response({"message": "Invalid id"}, 400)

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

        if not selected_obj:
            return Response({"message": "Invalid id"}, 400)

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
        configuration = AppConfiguration.objects.first()
        number_of_batches = configuration.number_of_batches if configuration else 0
        count = 0
        for count, image in enumerate(
                Image.objects.filter(is_accepted=True,
                                     deleted=False).order_by('?')):
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
        enumerators_group = configuration.enumerators_group if configuration else None
        validators_group = configuration.validators_group if configuration else None
        number_of_batches = configuration.number_of_batches if configuration else None

        if not (enumerators_group and validators_group):
            return Response({"message": "Invalid groups"}, 400)

        # Reset all assigned image batch
        User.objects.filter(assigned_image_batch__gt=-1).update(
            assigned_audio_batch=-1, assigned_image_batch=-1)

        count = -1
        for count, user in enumerate(enumerators_group.user_set.all().order_by(
                "id")):  # type: ignore
            user.assigned_image_batch = count % number_of_batches + 1  # type: ignore
            user.save()

        # Assign audio batches
        for user in validators_group.user_set.all().order_by(
                "id"):  # type: ignore
            if user.assigned_image_batch >= 0:  # Else this user wasn't assigned a batch of images hence can validate any batch
                user.assigned_audio_batch = (user.assigned_image_batch +
                                             1) % number_of_batches
                user.save()

        return Response({
            "message":
            f"Shuffled {count + 1} users among {number_of_batches} batches."
        })


class WebAppConfigurations(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        config = AppConfiguration.objects.first()
        if config:
            return Response({
                "message": "Web app configurations",
                "configurations": {
                    "android_apk_url":
                    request.build_absolute_uri(config.android_apk.url)
                    if config.android_apk else "",
                }
            })
        return Response({}, 404)


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


class ImagePreviewNavigation(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get(self, request, *args, **kwargs):
        current_image_id = request.GET.get("current_image_id", 0)
        direction = request.GET.get("direction", "next")

        images = Image.objects.all(deleted=False).order_by("id")

        # Use filters from query param
        filters = request.GET.get("filters")
        query = request.GET.get("query") or request.GET.get("q")

        if filters:
            images = apply_filters(images, filters)
        if query and hasattr(Image, "generate_query"):
            images = images.filter(Image.generate_query(query))

        if "prev" in direction:
            image = images.filter(id__lt=current_image_id).last()
        else:
            image = images.filter(id__gt=current_image_id).first()

        data = self.serializer_class(image, context={
            "request": request
        }).data if image else None
        return Response({
            "image": data,
        })


class ExportAudioData(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ["setup.manage_setup"]

    def get(self, request, *args, **kwargs):
        base_url = request.build_absolute_uri("/").strip("/")

        export_audio_data.delay(user_id=request.user.id,
                                data=request.data,
                                base_url=base_url)  # type: ignore

        return Response({
            "message":
            "Audio export status. You'll receive a notification when done.",
        })


class GetDashboardStatistics(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        audios = Audio.objects.all()
        images = Image.objects.all(deleted=False)
        transcriptions = Transcription.objects.all()
        hours_in_seconds = 3600

        #disabled: yapf
        audios_submitted = audios.count()
        audios_approved = audios.filter(is_accepted=True).count()
        audios_transcribed = transcriptions.count()

        audios_hours_submitted = round(
            sum([audio.get("duration")
                 for audio in audios.values("duration")]) / hours_in_seconds,
            2)

        audios_hours_approved = round(
            sum([
                audio.get("duration")
                for audio in audios.filter(is_accepted=True).values("duration")
            ]) / hours_in_seconds, 2)

        unique_transcriptions = transcriptions
        try:
            if unique_transcriptions.distinct("audio").exists():
                unique_transcriptions = unique_transcriptions.distinct("audio")
        except NotSupportedError as e:
            logger.error(str(e))

        audios_hours_transcribed = round(
            sum([
                transcription.audio.duration
                for transcription in unique_transcriptions
            ]) / hours_in_seconds, 2)

        images_submitted = images.count()
        images_approved = images.filter(is_accepted=True).count()

        return Response({
            "statistics": {
                "audios_submitted": audios_submitted,
                "audios_approved": audios_approved,
                "audios_transcribed": audios_transcribed,
                "audios_hours_submitted": audios_hours_submitted,
                "audios_hours_approved": audios_hours_approved,
                "audios_hours_transcribed": audios_hours_transcribed,
                "images_submitted": images_submitted,
                "images_approved": images_approved,
            }
        })
