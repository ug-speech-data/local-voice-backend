from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from accounts.models import User, Wallet
from dashboard.models import Category, Image, Validation, Participant, Audio, Transcription, Notification
from setup.models import AppConfiguration
from datetime import datetime
from django.utils.timezone import make_aware
from payments.models import Transaction


class UserSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return obj.groups.values_list("name", flat=True)

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
            "id",
            "email_address",
            "photo_url",
            "created_at",
            "short_name",
            "last_login_date",
            "phone",
            "surname",
            "locale",
            'assigned_image_batch',
            "other_names",
            "groups",
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

    def get_demo_video_url(self, obj):
        request = self.context.get("request")
        if obj.demo_video:
            return request.build_absolute_uri(obj.demo_video.url)
        return ""

    class Meta:
        model = AppConfiguration
        exclude = [
            "demo_video",
            "sms_sender_id",
            "api_key",
            "send_sms",
            "required_image_validation_count",
            "required_audio_validation_count",
            "required_transcription_validation_count",
            "required_image_description_count",
            "number_of_batches",
            "enumerators_group",
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
        return group.permissions.filter(id=obj.id).exists()

    class Meta:
        model = Permission
        fields = "__all__"


class AppConfigurationSerializer(serializers.ModelSerializer):
    demo_video_url = serializers.SerializerMethodField()
    enumerators_group = GroupSerializer(read_only=True)

    def get_demo_video_url(self, obj):
        request = self.context.get("request")
        if obj.demo_video:
            return request.build_absolute_uri(obj.demo_video.url)
        return ""

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

    def get_category(self, obj):
        if obj.categories.first():
            return obj.categories.first().name
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


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = "__all__"