from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import User, Participant
from rest_api.models import MobileAppConfiguration


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email_address",
            "photo",
            "created_at",
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
    