from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from accounts.models import Participant, User
from dashboard.models import Category
from rest_api.models import MobileAppConfiguration


class UserSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()

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
            "other_names",
        ]


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email_address",
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


class ParticipantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Participant
        fields = ['id', 'gender', 'age', 'user', 'local_id']
        extra_kwargs = {"id": {"read_only": True}}

    def create(self, validated_data):
        Participant = self.Meta.model(**validated_data)
        Participant.save()
        return Participant


class MobileAppConfigurationSerializer(serializers.ModelSerializer):
    demo_video_url = serializers.SerializerMethodField()

    def get_demo_video_url(self, obj):
        request = self.context.get("request")
        if obj.demo_video:
            return request.build_absolute_uri(obj.demo_video.url)
        return ""

    class Meta:
        model = MobileAppConfiguration
        exclude = ["demo_video"]


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
