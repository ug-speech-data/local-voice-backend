import json
import logging

from django.db import transaction
from django.db.models import Count, Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import User
from dashboard.models import (Audio, AudioTranscriptionAssignment,
                              AudioValidationAssignment, Image)
from local_voice.utils.constants import ValidationStatus
from rest_api.serializers import (AudioSerializer, AudioUploadSerializer,
                                  ImageSerializer,
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
        restricted_audio_count = request.user.restricted_audio_count
        configuration = AppConfiguration.objects.first()
        number_of_batches = configuration.number_of_batches if configuration else 8

        if not batch_number or batch_number <= 0 or batch_number > number_of_batches:
            result = User.objects.filter(
                assigned_image_batch__gt=0,
                assigned_image_batch__lte=number_of_batches).values(
                    'assigned_image_batch').annotate(
                        total=Count('id')).order_by('total')

            result = sorted(result, key=lambda item: item.get("total"))
            least_used_batch = result[0].get("assigned_image_batch")

            user = request.user
            user.assigned_image_batch = least_used_batch
            batch_number = least_used_batch
            user.save()

        if batch_number > 0:
            images = images.filter(batch_number=batch_number)

        if restricted_audio_count > 0 and restricted_audio_count < 125:
            images = images.order_by("id")[:restricted_audio_count]

        data = self.serializer_class(images,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"images": data})


class GetUploadedAudios(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AudioSerializer

    def get(self, request, *args, **kwargs):
        audios = Audio.objects.filter(submitted_by=request.user, deleted=False)
        data = self.serializer_class(audios,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"audios": data})


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
            saved, response = serializer.create(request)
            if saved:
                return Response({
                    "audio":
                    AudioSerializer(response, context={
                        "request": request
                    }).data,
                    "success":
                    True,
                    "message":
                    "Audio uploaded successfully"
                })
            else:
                logger.error(response)
                return Response({"success": False, "message": response}, 400)
        else:
            error_messages = []
            for field, errors in serializer.errors.items():
                error_messages.append(f"{field}: " + str(errors))
            logger.error(error_messages)
            return Response({"error_messages": error_messages}, 400)


class GetBulkAssignedToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AudioSerializer

    ##############################################################
    # NOTE: Caching will return audios that may have been validated by the users
    # and deleted from their device resulting in double validation
    # The app sends request every ~30 minutes to this endpoint automatically.
    # Users can trigger this requests too by themselves.
    ##############################################################
    # @method_decorator(cache_page(60 * 2* 15))
    # @method_decorator(vary_on_headers(*["Authorization"]))
    def get(self, request, *args, **kwargs):
        count = min(request.data.get("count") or 480, 1000)
        completed = "true" in request.GET.get("completed", "")
        configuration = AppConfiguration.objects.first()
        required_audio_validation_count = configuration.required_audio_validation_count if configuration else 0
        assignment, created = AudioValidationAssignment.objects.get_or_create(
            user=request.user)

        if created or assignment.audios.all().count() == 0 or completed:
            audios = Audio.objects.select_for_update().annotate(c=Count("assignments"), val_count=Count("validations")) \
                    .filter(c__lt=required_audio_validation_count) \
                    .filter(audio_status = ValidationStatus.PENDING.value,
                            deleted=False,
                                is_accepted=False,
                                rejected=False,
                                val_count__lt=required_audio_validation_count,
                            locale=request.user.locale) \
                    .exclude(Q(validations__user=request.user)|Q(submitted_by=request.user))\
                    .order_by("-val_count", "image", "id")[:count]
            assignment.audios.set(audios)
            assignment.save()
        audios = assignment.audios.annotate(val_count=Count("validations")).filter(
            audio_status=ValidationStatus.PENDING.value,
            val_count__lt=required_audio_validation_count,
            deleted=False).exclude(Q(validations__user=request.user))\
            .order_by("-val_count", "image", "id")

        data = self.serializer_class(audios,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"audios": data})


class GetBulkAssignedToTranscribe(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AudioSerializer

    ##############################################################
    # NOTE: Caching will return audios that may have been validated by the users
    # and deleted from their device resulting in double validation
    # The app sends request every ~30 minutes to this endpoint automatically.
    # Users can trigger this requests too by themselves.
    ##############################################################
    # @method_decorator(cache_page(60 * 2* 15))
    # @method_decorator(vary_on_headers(*["Authorization"]))
    def get(self, request, *args, **kwargs):
        count = min(request.data.get("count") or 480, 1000)
        completed = "true" in request.GET.get("completed", "")
        configuration = AppConfiguration.objects.first()
        required_transcription_validation_count = configuration.required_transcription_validation_count if configuration else 0
        assignment, created = AudioTranscriptionAssignment.objects.get_or_create(
            user=request.user)
        EXPECTED_TRANSCRIPTIONS_PER_IMAGE = 24 * required_transcription_validation_count

        locale_count = f"image__transcription_count_{request.user.locale}"
        if not hasattr(Image, f"transcription_count_{request.user.locale}"):
            return Response({"message": "Invalid locale"})

        transcription_count_filter = {
            f"{locale_count}__lt": EXPECTED_TRANSCRIPTIONS_PER_IMAGE
        }

        if created or assignment.audios.all().count() == 0 or completed:
            audios = (Audio.objects.annotate(
                t_assign=Count("transcriptions_assignments"),
                t_count=Count("transcriptions")).filter(
                    Q(**transcription_count_filter)
                    | Q(t_count__gte=1)).filter(
                        transcription_status=ValidationStatus.PENDING.value,
                        locale=request.user.locale,
                        deleted=False,
                        t_assign__lt=required_transcription_validation_count,
                        t_count__lt=required_transcription_validation_count).
                      exclude(Q(transcriptions__user=request.user)))[:count]
            assignment.audios.set(audios)
            assignment.save()
        audios = assignment.audios.annotate(
            t_count=Count("transcriptions")).filter(
                **transcription_count_filter,
                transcription_status=ValidationStatus.PENDING.value,
                t_count__lt=required_transcription_validation_count,
                deleted=False).exclude(
                    Q(transcriptions__user=request.user)).order_by(
                        "-t_count", locale_count, "?")

        data = self.serializer_class(audios,
                                     many=True,
                                     context={
                                         "request": request
                                     }).data
        return Response({"audios": data})