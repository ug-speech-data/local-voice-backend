from django.contrib.auth import authenticate, logout
from knox.models import AuthToken
from rest_api.models import MobileAppConfiguration
from rest_api.serializers import (LoginSerializer,
                                  MobileAppConfigurationSerializer,
                                  ParticipantSerializer, RegisterSerializer,
                                  UserSerializer)
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
