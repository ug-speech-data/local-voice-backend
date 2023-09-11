import logging
import math
from datetime import datetime

from django.contrib.auth.models import Group, Permission
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import transaction
from accounts.forms import GroupForm, UserForm
from accounts.models import User
from rest_api.tasks import (get_audios_pending,
                            get_audios_rejected,
                            get_audios_accepted,
                            get_audios_submitted,
                            get_audios_validated,
                            get_conflicts_resolved,
                            get_transcriptions_resolved,
                            get_audios_transcribed)
from rest_api.serializers import UserStatisticSerializer
from local_voice.utils.constants import TranscriptionStatus
from app_statistics.models import Statistics
from dashboard.forms import CategoryForm
from dashboard.models import (Audio, Category, Image, Notification,
                              Participant, Transcription)
from local_voice.utils.constants import ValidationStatus
from local_voice.utils.functions import (apply_filters, get_errors_from_form,
                                         relevant_permission_objects)
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (
    AppConfigurationSerializer, AudiosByLeadsSerializer, AudioSerializer,
    AudioTranscriptionSerializer, CategorySerializer,
    ConflictResolutionLeaderBoardSerializer, EnumeratorSerialiser,
    GroupPermissionSerializer, GroupSerializer, ImageSerializer,
    LimitedUserSerializer, NotificationSerializer, ParticipantSerializer,
    TranscriptionSerializer, UserSerializer, ValidationLeaderBoardSerializer)
from rest_api.tasks import export_audio_data
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration

logger = logging.getLogger("app")
QUERY_PAGE_SIZE = 10


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


class GetAudiosToTranscribe(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.transcribe_audio"]
    serializer_class = AudioTranscriptionSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else 2
        offset = request.GET.get("offset", -1)

        audio = Audio.objects.annotate(t_count=Count("transcriptions"), t_assign=Count("transcriptions_assignments")).filter(
            deleted=False,
            transcription_status=ValidationStatus.PENDING.value,
            t_assign__lt=required_transcription_validation_count,
            t_count__lt=required_transcription_validation_count,
            locale=request.user.locale)\
            .filter(Q(second_audio_status=ValidationStatus.ACCEPTED.value))\
            .exclude(Q(transcriptions__user=request.user) | Q(id=offset))\
            .order_by("image", "-t_count", "?")\
            .first()

        if audio:
            audio.transcription_status = ValidationStatus.IN_REVIEW.value
            audio.save()

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
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else 2
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
        "auth.add_group",
        "auth.change_group",
        "auth.view_group",
    ]
    serializer_class = GroupSerializer
    model_class = Group
    form_class = GroupForm
    response_data_label = "group"
    response_data_label_plural = "groups"

    def get(self, request):
        limited = "true" in request.GET.get("limited", "")
        configuration = AppConfiguration.objects.first()
        groups = Group.objects.all()
        if limited:
            groups = configuration.limited_groups.all(
            ) if configuration else Group.objects.none()

        response_data = {
            self.response_data_label_plural:
            self.serializer_class(groups,
                                  context={
                                      "request": request
                                  },
                                  many=True).data,
        }
        return Response(response_data)


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
    add_permissions = ["accounts.add_user"]
    change_permissions = ["accounts.change_user"]
    delete_permissions = ["accounts.delete_user"]

    serializer_class = UserSerializer
    model_class = User
    form_class = UserForm
    response_data_label = "user"
    response_data_label_plural = "users"

    def post(self, request, *args, **kwargs):
        is_active = request.data.get("is_active", None)
        obj_id = request.data.get("id")
        lead_email_address = request.data.get("lead_email_address")
        new_password = request.data.get("password")
        group_names = request.data.get("groups")
        groups = Group.objects.filter(name__in=group_names)
        obj = None
        created_by = None
        if obj_id:
            obj = self.model_class.objects.filter(id=obj_id).first()
            if is_active != None:
                obj.is_active = is_active
                obj.save()
        else:
            created_by = request.user

        lead = User.objects.filter(email_address=lead_email_address,
                                   deleted=False).first()
        if not lead and lead_email_address:
            return Response({
                "message":
                "Lead not found.",
                "error_message":
                f"Lead with email address {lead_email_address} not found.",
            })

        form = self.form_class(request.data, instance=obj)
        if form.is_valid():
            user = form.save()
            if new_password and len(new_password) > 0:
                user.set_password(new_password)
            user.groups.set(groups)
            user.updated_by = request.user
            user.lead = lead
            if created_by:
                user.created_by = created_by
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
        default_user_group_name = request.data.get("default_user_group_name")

        enumerators_group = Group.objects.filter(
            name=enumerators_group_name).first()
        validators_group = Group.objects.filter(
            name=validators_group_name).first()
        default_user_group = Group.objects.filter(
            name=default_user_group_name).first()

        configuration, _ = AppConfiguration.objects.get_or_create()

        try:
            for key, value in request.data.items():
                if not value:
                    continue
                if hasattr(configuration, key):
                    if type(getattr(configuration, key)) == bool:
                        setattr(configuration, key, value == "true")
                    else:
                        setattr(configuration, key, value)
            configuration.enumerators_group = enumerators_group
            configuration.validators_group = validators_group
            configuration.default_user_group = default_user_group
            configuration.save()
        except Exception as e:
            print(e)
            logger.error(str(e))
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
    add_permissions = ["dashboard.add_image"]
    change_permissions = ["dashboard.change_image"]
    delete_permissions = ["dashboard.delete_image"]

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
        image_obj.main_category = Category.objects.filter(
            name=category_names[0]).first()
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
    required_permissions = ["setup.manage_collected_data"]

    serializer_class = AudioSerializer
    model_class = Audio
    response_data_label = "audio"
    response_data_label_plural = "audios"

    def post(self, request, *args, **kwargs):
        object_id = request.data.pop("id") or -1
        audio_obj = self.model_class.objects.filter(id=object_id,
                                                    deleted=False).first()

        if not audio_obj:
            return Response({"message": "Invalid image id"}, 400)

        status = request.data.get("status")
        if status == "accept":
            audio_obj.rejected = False
            audio_obj.is_accepted = True
            audio_obj.second_audio_status = ValidationStatus.ACCEPTED.value
        else:
            audio_obj.rejected = True
            audio_obj.is_accepted = False
            audio_obj.second_audio_status = ValidationStatus.REJECTED.value

        if not audio_obj.conflict_resolved_by:
            audio_obj.conflict_resolved_by = request.user

        audio_obj.save()

        return Response({
            "message":
            "Audio update successfully",
            self.response_data_label:
            self.serializer_class(audio_obj, context={
                "request": request
            }).data
        })


class CollectedTranscriptionsAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_collected_data"]

    serializer_class = AudioTranscriptionSerializer
    model_class = Audio
    response_data_label = "audios"
    response_data_label_plural = "audios"

    def modify_response_data(self, objects):
        return objects.annotate(t_count=Count("transcriptions")).filter(
            t_count__gt=0)

    def get(self, request, *args, **kwargs):
        filters = request.GET.getlist("filters")
        query = request.GET.get("query") or request.GET.get("q")

        objects = self.model_class.objects.all().order_by(
            "-id")  # type: ignore
        if filters:
            objects = apply_filters(objects, filters)
        if query and hasattr(self.model_class,
                             "generate_query"):  # type: ignore
            objects = objects.filter(
                Q(transcriptions__user__email_address__contains=query)
                | Q(transcriptions__user__surname__contains=query)
                | Q(transcriptions__user__other_names__contains=query)
            )  # type: ignore

        if hasattr(self.model_class, "deleted"):  # type: ignore
            objects = objects.filter(deleted=False)

        if hasattr(self, "modify_response_data"):
            objects = self.modify_response_data(objects)

        page = request.GET.get("page", "")
        page_size = request.GET.get("page_size", "")
        page_size = int(
            page_size) if page_size.isnumeric() else QUERY_PAGE_SIZE
        total_pages = max(1, math.ceil(objects.count() / page_size))

        page = int(page) if page.isnumeric() else 1
        if page > total_pages:
            page = total_pages
        page = max(page, 1)

        paginated_objects = objects[(page - 1) * page_size:page * page_size]
        prev_page = page - 1 if page > 1 else None
        next_page = page + 1 if total_pages > page else None

        # yapf: disable
        response_data = {
            self.response_data_label_plural:
            self.serializer_class(paginated_objects, context={
                                  "request": request}, many=True).data,
            "page": page,
            "page_size": page_size,
            "total": objects.count(),
            "next_page": next_page,
            "previous_page": prev_page,
            "total_pages": total_pages,
        }
        return Response(response_data)

    def post(self, request, *args, **kwargs):
        object_id = request.data.get("id") or -1
        corrected_text = request.data.get("text")
        transcription_status = request.data.get("transcription_status")
        audio = self.model_class.objects.filter(id=object_id).first()

        if not audio:
            return Response({"message": "Invalid id"}, 400)

        # Update
        if transcription_status and corrected_text:
            corrected_text = " ".join(
                corrected_text.replace("\r", "").replace("\n", "").split())
            transcriptions = audio.transcriptions.all()
            transcriptions.update(corrected_text=corrected_text)
            transcriptions.filter(conflict_resolved_by=None).update(
                conflict_resolved_by=request.user)

        audio.transcription_status = transcription_status
        audio.save()

        return Response({
            "message":
            "Transcription update successfully",
            self.response_data_label:
            self.serializer_class(audio, context={
                "request": request
            }).data
        })


class CollectedParticipantsAPI(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_collected_data"]

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
        filter_accepted = request.GET.get("is_accepted", False)
        configuration = AppConfiguration.objects.first()
        number_of_batches = configuration.number_of_batches if configuration else 0
        count = 0

        images = Image.objects.filter(deleted=False)

        if filter_accepted:
            images = images.filter(is_accepted=True)

        for count, image in enumerate(images.order_by('?')):
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
            is_read=False, user=request.user).order_by("-created_at")[:30]
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

        images = Image.objects.filter(deleted=False).order_by("id")

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

    def post(self, request, *args, **kwargs):
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

    def language_statistics_in_hours(self, lang):
        stats = Statistics.objects.first()
        # yapf: disable
        return {
            f"{lang}_audios_submitted_in_hours": getattr(stats, f"{lang}_audios_submitted_in_hours"),
            f"{lang}_audios_single_validation_in_hours": getattr(stats, f"{lang}_audios_single_validation_in_hours"),
            f"{lang}_audios_double_validation_in_hours": getattr(stats, f"{lang}_audios_double_validation_in_hours"),
            f"{lang}_audios_validation_conflict_in_hours": getattr(stats, f"{lang}_audios_validation_conflict_in_hours"),
            f"{lang}_audios_approved_in_hours": getattr(stats, f"{lang}_audios_approved_in_hours"),
            f"{lang}_audios_rejected_in_hours": int(getattr(stats, f"{lang}_audios_single_validation_in_hours")) - int(getattr(stats, f"{lang}_audios_approved_in_hours")),
            f"{lang}_audios_transcribed_in_hours": getattr(stats, f"{lang}_audios_transcribed_in_hours"),
            f"{lang}_audios_transcribed_in_hours_unique": getattr(stats, f"{lang}_audios_transcribed_in_hours_unique"),
        }

    def language_statistics(self, lang):
        stats = Statistics.objects.first()
        # yapf: disable

        rejected = max(0, float(getattr(
            stats, f"{lang}_audios_single_validation")) - float(getattr(stats, f"{lang}_audios_approved")))
        return {
            f"{lang}_audios_submitted": getattr(stats, f"{lang}_audios_submitted"),
            f"{lang}_audios_single_validation": getattr(stats, f"{lang}_audios_single_validation"),
            f"{lang}_audios_double_validation": getattr(stats, f"{lang}_audios_double_validation"),
            f"{lang}_audios_validation_conflict": getattr(stats, f"{lang}_audios_validation_conflict"),
            f"{lang}_audios_approved": getattr(stats, f"{lang}_audios_approved"),
            f"{lang}_audios_rejected_percentage": round(rejected / max(1, float(getattr(stats, f"{lang}_audios_single_validation"))) * 100, 2),
            f"{lang}_audios_transcribed": getattr(stats, f"{lang}_audios_transcribed"),
            f"{lang}_audios_transcribed_unique": getattr(stats, f"{lang}_audios_transcribed_unique"),
        }

    @method_decorator(cache_page(60 * 10))
    def get(self, request, *args, **kwargs):
        stats, _ = Statistics.objects.get_or_create()
        conflict_resolution_users = User.objects.filter(
            conflicts_resolved__gt=0).order_by("-conflicts_resolved")[:15]
        validation_users = User.objects.filter().order_by(
            "-audios_validated")[:15]

        lead_ids = User.objects.filter(deleted=False).exclude(
            lead=None).values_list("lead_id", flat=True)
        leads = User.objects.filter(id__in=lead_ids).order_by(
            "-proxy_audios_submitted_in_hours")

        return Response({
            "updated_at": stats.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": {
                "audios_submitted": stats.audios_submitted,
                "audios_approved": stats.audios_approved,
                "audios_hours_submitted": stats.audios_hours_submitted,
                "audios_hours_approved": stats.audios_hours_approved,
                "audios_transcribed": stats.audios_transcribed,
                "audios_hours_transcribed": stats.audios_hours_transcribed,
                "audios_transcribed_unique": stats.audios_transcribed_unique,
                "audios_hours_transcribed_unique": stats.audios_hours_transcribed_unique,
                "images_submitted": stats.images_submitted,
                "images_approved": stats.images_approved,
            },

            "language_statistics": {
                "ewe": self.language_statistics("ewe"),
                "akan": self.language_statistics("akan"),
                "dagbani": self.language_statistics("dagbani"),
                "dagaare": self.language_statistics("dagaare"),
                "ikposo": self.language_statistics("ikposo"),
            },

            "language_statistics_in_hours": {
                "ewe": self.language_statistics_in_hours("ewe"),
                "akan": self.language_statistics_in_hours("akan"),
                "dagbani": self.language_statistics_in_hours("dagbani"),
                "dagaare": self.language_statistics_in_hours("dagaare"),
                "ikposo": self.language_statistics_in_hours("ikposo"),
            },
            "conflict_resolution_leaders": ConflictResolutionLeaderBoardSerializer(conflict_resolution_users, many=True).data,
            "validation_leaders": ValidationLeaderBoardSerializer(validation_users, many=True).data,
            "audios_by_leads": AudiosByLeadsSerializer(leads, many=True).data,
        })


class GetEnumerators(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnumeratorSerialiser

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_headers(*["Authorization"]))
    def get(self, request, *args, **kwargs):
        users = User.objects.filter(
            Q(lead=request.user), deleted=False).order_by("surname")
        return Response(
            {"enumerators": self.serializer_class(users, many=True).data})


class LimitedUsersAPIView(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.approve_sample_audio_recorders"]

    serializer_class = LimitedUserSerializer
    model_class = User
    response_data_label = "user"
    response_data_label_plural = "users"

    def modify_response_data(self, objects):
        return objects.filter(restricted_audio_count__gt=0)

    def post(self, request, *args, **kwargs):
        """Remove limitation"""
        object_id = request.data.get("user_id") or -1
        user = self.model_class.objects.filter(id=object_id).first()

        if not user:
            return Response({"message": "Invalid id"}, 400)

        # Negative number if used as unrestricted when filtering image.
        user.restricted_audio_count = -1
        user.save()

        return Response({
            "message":
            "User updated successfully",
            self.response_data_label:
            self.serializer_class(user, context={
                "request": request
            }).data
        })


class GetAudioTranscriptionToResolve(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.resolve_transcription"]
    serializer_class = AudioTranscriptionSerializer

    def get(self, request, *args, **kwargs):
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else 2
        offset = request.GET.get("offset", -1)

        with transaction.atomic():
            audio = Audio.objects.annotate(t_count=Count("transcriptions")).filter(
                deleted=False,
                second_audio_status=ValidationStatus.ACCEPTED.value,
                transcription_status=TranscriptionStatus.CONFLICT.value,
                t_count__gte=required_transcription_validation_count,
                locale=request.user.locale)\
                .exclude(Q(transcriptions__user=request.user) | Q(id=offset))\
                .order_by("-t_count", "?")\
                .first()
            if audio:
                audio.transcription_status = ValidationStatus.IN_REVIEW.value
                audio.save()
        data = self.serializer_class(audio, context={
            "request": request
        }).data if audio else None
        return Response({
            "audio": data,
        })

    def post(self, request, *args, **kwargs):
        object_id = request.data.get("id") or -1
        corrected_text = request.data.get("text")
        transcription_status = request.data.get("transcription_status")
        audio = Audio.objects.filter(id=object_id).first()

        if not audio:
            return Response({"message": "Invalid id"}, 400)

        # Update
        if transcription_status and corrected_text:
            corrected_text = " ".join(
                corrected_text.replace("\r", "").replace("\n", "").split())
            transcriptions = audio.transcriptions.all()
            transcriptions.update(corrected_text=corrected_text)
            transcriptions.filter(conflict_resolved_by=None).update(
                conflict_resolved_by=request.user)

        audio.transcription_status = transcription_status
        audio.save()

        return Response({
            "message":
            "Transcription update successfully",
            "status": "success",
            "audio":
            self.serializer_class(audio, context={
                "request": request
            }).data
        })


class SearchUser(generics.GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        query = request.GET.get("query")
        users = User.objects.filter(deleted=False, is_active=True).filter(Q(surname__icontains=query) |
                                                                          Q(other_names__icontains=query) |
                                                                          Q(phone=query))
        users = users[:5]
        return Response({
            "users": self.serializer_class(users, context={
                "request": request
            }, many=True).data,
        })


class GetUserStatistics(SimpleCrudMixin):
    serializer_class = UserStatisticSerializer
    required_permissions = ["setup.view_user_stats"]
    model_class = User
    response_data_label = "user"
    response_data_label_plural = "users"

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({
                "message": "User not found."
            })
        user.audios_rejected = get_audios_rejected(user)
        user.audios_pending = get_audios_pending(user)
        user.audios_accepted = get_audios_accepted(user)
        user.audios_submitted = get_audios_submitted(user)
        user.audios_validated = get_audios_validated(user)
        user.conflicts_resolved = get_conflicts_resolved(user)
        user.transcriptions_resolved = get_transcriptions_resolved(user)
        user.audios_transcribed = get_audios_transcribed(user)
        user.save()

        return Response({
            "message": "User stat updated."
        })


class ArchiveUser(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        user = User.objects.filter(id=user_id).first()
        if user:
            user.archived = not user.archived
            user.save()
        else:
            return Response({
                "message": "User not found."
            })
        return Response({
            "message": "User updated."
        })
