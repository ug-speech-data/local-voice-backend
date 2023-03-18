import json
import logging
from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from django.utils.timezone import make_aware
from rest_framework import serializers

from accounts.models import User, Wallet
from dashboard.models import (Audio, Category, Image, Notification,
                              Participant, Transcription, Validation)
from payments.models import Transaction
from setup.models import AppConfiguration

logger = logging.getLogger("app")


class UserSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    audios_submitted = serializers.SerializerMethodField()
    audios_validated = serializers.SerializerMethodField()

    def get_balance(self, user):
        if user.wallet:
            return str(user.wallet.balance)
        return 0

    def get_audios_submitted(self, user):
        from dashboard.models import Audio
        return Audio.objects.filter(submitted_by=user).count()

    def get_audios_validated(self, user):
        from dashboard.models import Audio
        return Audio.objects.filter(validations__user=user,
                                    validations__is_valid=True).count()

    def get_groups(self, obj):
        return obj.groups.values_list("name", flat=True)

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"

    def get_short_name(self, obj):
        return obj.email_address.split("@")[0]

    def get_user_permissions(self, user):
        permissions = []
        for perm in user.get_all_permissions():
            permissions.append(perm.split(".")[-1])
        return sorted(permissions)

    class Meta:
        model = User
        exclude = [
            "password",
            "is_staff",
            "is_superuser",
            "is_active",
            "wallet",
        ]


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email_address",
            "locale",
            "phone",
            "surname",
            "other_names",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = self.Meta.model(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email_address = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class MobileAppConfigurationSerializer(serializers.ModelSerializer):
    demo_video_url = serializers.SerializerMethodField()
    participant_privacy_statement_audio = serializers.SerializerMethodField()

    def get_demo_video_url(self, obj):
        request = self.context.get("request")
        locale = request.user.locale if request and request.user else ""
        if "ee_gh" in locale and obj.demo_video_ewe:
            return request.build_absolute_uri(obj.demo_video_ewe.url)

        if "ak_gh" in locale and obj.demo_video_akan:
            return request.build_absolute_uri(obj.demo_video_akan.url)

        if "dag_gh" in locale and obj.demo_video_dagaare:
            return request.build_absolute_uri(obj.demo_video_dagaare.url)

        if "dga_gh" in locale and obj.demo_video_dagbani:
            return request.build_absolute_uri(obj.demo_video_dagbani.url)

        if "kpo_gh" in locale and obj.demo_video_ikposo:
            return request.build_absolute_uri(obj.demo_video_ikposo.url)
        return ""

    def get_participant_privacy_statement_audio(self, obj):
        request = self.context.get("request")
        locale = request.user.locale if request and request.user else ""
        if "ee_gh" in locale and obj.participant_privacy_statement_audio_ewe:
            return request.build_absolute_uri(
                obj.participant_privacy_statement_audio_ewe.url)

        if "ak_gh" in locale and obj.participant_privacy_statement_audio_akan:
            return request.build_absolute_uri(
                obj.participant_privacy_statement_audio_akan.url)

        if "dag_gh" in locale and obj.participant_privacy_statement_audio_dagaare:
            return request.build_absolute_uri(
                obj.participant_privacy_statement_audio_dagaare.url)

        if "dga_gh" in locale and obj.participant_privacy_statement_audio_dagbani:
            return request.build_absolute_uri(
                obj.participant_privacy_statement_audio_dagbani.url)

        if "kpo_gh" in locale and obj.participant_privacy_statement_audio_ikposo:
            return request.build_absolute_uri(
                obj.participant_privacy_statement_audio_ikposo.url)
        return ""

    class Meta:
        model = AppConfiguration
        fields = [
            "allow_saving_less_than_required_per_participant",
            "allow_recording_more_than_required_per_participant",
            "number_of_audios_per_participant",
            "max_audio_validation_per_user",
            "demo_video_url",
            "participant_privacy_statement_audio",
            "max_background_noise_level",
            "participant_privacy_statement",
            "id",
        ]


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = "__all__"


class GroupPermissionSerializer(serializers.ModelSerializer):
    group_has = serializers.SerializerMethodField()

    def get_group_has(self, obj):
        group = self.context.get("group")
        return group.permissions.filter(id=obj.id).exists() if group else []

    class Meta:
        model = Permission
        fields = "__all__"


class AppConfigurationSerializer(serializers.ModelSerializer):
    enumerators_group = GroupSerializer(read_only=True)
    validators_group = GroupSerializer(read_only=True)

    class Meta:
        model = AppConfiguration
        fields = "__all__"


class ValidationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.email_address

    class Meta:
        model = Validation
        fields = ["user", "is_valid"]


class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    validations = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    width = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

    def get_category(self, obj):
        if obj.main_category:
            return obj.main_category.name
        return ""

    def get_thumbnail(self, obj):
        request = self.context.get("request")
        if obj.thumbnail:
            return request.build_absolute_uri(obj.thumbnail.url)
        return self.get_image_url(obj)

    def get_height(self, obj):
        if obj.file:
            return obj.file.height
        return 0

    def get_width(self, obj):
        if obj.file:
            return obj.file.width
        return 0

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.file:
            return request.build_absolute_uri(obj.file.url)
        return ""

    def get_validations(self, obj):
        request = self.context.get("request")
        validations = obj.validations.all()
        return ValidationSerializer(validations,
                                    many=True,
                                    context={
                                        "request": request
                                    }).data

    class Meta:
        model = Image
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = "__all__"


class ParticipantSerializer(serializers.ModelSerializer):
    transaction = TransactionSerializer(read_only=True)
    submitted_by = serializers.SerializerMethodField()
    audio_count = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

    def get_submitted_by(self, obj):
        if obj.submitted_by:
            return obj.submitted_by.email_address
        return ""

    def get_audio_count(self, obj):
        return obj.audios.count()

    class Meta:
        model = Participant
        fields = "__all__"


class AudioSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    validations = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    submitted_by = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()
    image_batch_number = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

    def get_image_batch_number(self, obj):
        return obj.image.batch_number

    def get_audio_url(self, obj):
        request = self.context.get("request")
        if obj.file:
            return request.build_absolute_uri(obj.file.url)
        return ""

    def get_submitted_by(self, obj):
        if obj.submitted_by:
            return obj.submitted_by.email_address
        return ""

    def get_name(self, obj):
        if obj.file and obj.file.name:
            return obj.file.name.split("/")[-1]
        return "No file"

    def get_thumbnail(self, obj):
        request = self.context.get("request")
        if obj.image.thumbnail:
            return request.build_absolute_uri(obj.image.thumbnail.url)
        return self.get_image_url(obj)

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image.file:
            return request.build_absolute_uri(obj.image.file.url)
        return ""

    def get_validations(self, obj):
        request = self.context.get("request")
        validations = obj.validations.all()
        return ValidationSerializer(validations,
                                    many=True,
                                    context={
                                        "request": request
                                    }).data

    class Meta:
        model = Audio
        fields = "__all__"


class TranscriptionSerializer(serializers.ModelSerializer):
    audio = AudioSerializer(read_only=True)
    participant = ParticipantSerializer(read_only=True)
    submitted_by = serializers.SerializerMethodField()
    validations = serializers.SerializerMethodField()

    def get_validations(self, obj):
        request = self.context.get("request")
        validations = obj.validations.all()
        return ValidationSerializer(validations,
                                    many=True,
                                    context={
                                        "request": request
                                    }).data

    def get_submitted_by(self, obj):
        if obj.user:
            return obj.user.email_address
        return ""

    class Meta:
        model = Transcription
        fields = "__all__"


def time_ago(datetime_from):
    diff = make_aware(datetime.now()) - datetime_from
    total_seconds = diff.total_seconds()
    seconds = int(total_seconds % 60)
    minutes = int(total_seconds // 60)
    hours = int(total_seconds // (60 * 60))
    days = int(total_seconds // (60 * 60 * 24))

    if days:
        return f"{days} day(s) ago"
    if hours:
        return f"{hours} hour(s) ago"

    if minutes:
        return f"{minutes} minute(s) ago"

    return f"{seconds} second(s) ago"


class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    def get_time_ago(self, obj):
        return time_ago(obj.created_at)

    class Meta:
        model = Notification
        fields = "__all__"


class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = "__all__"


class PaymentUserSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    accrued_amount = serializers.SerializerMethodField()
    total_payout = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()
    wallet_last_updated_at = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        return obj.fullname

    def get_wallet_last_updated_at(self, obj):
        if not obj.wallet:
            obj.wallet = Wallet.objects.create()
            obj.save()
        return time_ago(obj.wallet.updated_at)

    def get_accrued_amount(self, obj):
        if not obj.wallet:
            obj.wallet = Wallet.objects.create()
            obj.save()
        return str(obj.wallet.accrued_amount)

    def get_total_payout(self, obj):
        if not obj.wallet:
            obj.wallet = Wallet.objects.create()
            obj.save()
        return str(obj.wallet.total_payout)

    def get_balance(self, obj):
        if not obj.wallet:
            obj.wallet = Wallet.objects.create()
            obj.save()
        return str(obj.wallet.balance)

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"

    def get_short_name(self, obj):
        return obj.email_address.split("@")[0]

    class Meta:
        model = User
        fields = [
            "id", "email_address", "photo_url", "short_name", "phone",
            "surname", "other_names", "accrued_amount", "total_payout",
            "balance", "fullname", "wallet_last_updated_at"
        ]


class AudioUploadSerializer(serializers.Serializer):

    class _AudioSerializer(serializers.Serializer):
        remoteImageID = serializers.IntegerField()
        duration = serializers.IntegerField()
        device_id = serializers.CharField()
        environment = serializers.CharField()

    class _ParticipantSerializer(serializers.Serializer):
        momoNumber = serializers.CharField(max_length=10)
        network = serializers.ChoiceField(["MTN", "VODAFONE", "AIRTELTIGO"])
        fullname = serializers.CharField(max_length=200)
        gender = serializers.CharField(max_length=200)
        age = serializers.IntegerField()
        acceptedPrivacyPolicy = serializers.BooleanField(default=True)

    api_client = serializers.CharField(max_length=30,
                                       required=False,
                                       default="Kotlin")
    audio_file = serializers.FileField()
    audio_data = _AudioSerializer()
    participant_data = _ParticipantSerializer(required=False)

    def create(self, request):
        file = request.FILES.get("audio_file")
        api_client = request.data.get("api_client")
        audio_data = request.data.get("audio_data")
        if audio_data and type(audio_data) == str:
            audio_data = json.loads(audio_data)
        else:
            return False, "No audio data"
        participant_data = request.data.get("participant_data")
        if participant_data and type(participant_data) == str:
            participant_data = json.loads(participant_data)

        image_id = audio_data.get("remoteImageID", -1)
        image_object = Image.objects.filter(id=image_id).first()
        participant_object = None

        if not image_object:
            return False, "Invalid Image ID"

        if not file:
            return False, "No file"

        try:
            if participant_data:
                participant_object, created = Participant.objects.get_or_create(
                    momo_number=participant_data.get("momoNumber"),
                    network=participant_data.get("network", ""),
                    fullname=participant_data.get("fullname"),
                    gender=participant_data.get("gender"),
                    submitted_by=request.user,
                    age=participant_data.get("age"),
                    accepted_privacy_policy=participant_data.get(
                        "acceptedPrivacyPolicy", False),
                    api_client=api_client,
                )
            if image_object and file and audio_data:
                audio = Audio.objects.create(
                    image=image_object,
                    submitted_by=request.user,
                    file=file,
                    duration=audio_data.get("duration"),
                    locale=request.user.locale,
                    device_id=audio_data.get("device_id"),
                    environment=audio_data.get("environment"),
                    participant=participant_object,
                    api_client=api_client)

                # Update user's wallet.
                configuration = AppConfiguration.objects.first()
                if not participant_object:
                    # Audio was recording by the user themselves.
                    amount = configuration.individual_audio_aggregators_amount_per_audio if configuration else 0
                else:
                    amount = configuration.audio_aggregators_amount_per_audio if configuration else 0

                # Credit user(enumerators) account.
                if audio.submitted_by.wallet:
                    audio.submitted_by.wallet.credit_wallet(amount)

                participant_object.update_amount()

        except Exception as e:
            logger.error(e)
            return False, str(e)
        return True, "Success"


class EnumeratorSerialiser(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        return f"{obj.surname} {obj.other_names}"

    class Meta:
        model = User
        fields = [
            "id",
            "fullname",
        ]
