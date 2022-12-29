from random import sample
from time import sleep

from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response

from accounts.forms import GroupForm, UserForm
from accounts.models import User
from rest_api.serializers import AppConfigurationSerializer
from local_voice.utils.functions import get_errors_from_form
from dashboard.forms import CategoryForm
from dashboard.models import Category
from local_voice.utils.functions import relevant_permission_objects
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (CategorySerializer,
                                  GroupPermissionSerializer, GroupSerializer,
                                  UserSerializer)
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration


class GetImagesToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_image"]

    def get(self, request, *args, **kwargs):
        images = [
            {
                "id":
                6,
                "name":
                "image6",
                "image_url":
                "http://cdn.cnn.com/cnnnext/dam/assets/180508141319-03-amazing-places-africa---victoria-falls.jpg",
            },
            {
                "id":
                1,
                "name":
                "image1",
                "image_url":
                "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
            },
            {
                "id":
                2,
                "name":
                "image2",
                "image_url":
                "https://www.gravatar.com/avatar/e5ea2c87d14565ecfec13c3db67428a2?s=256&d=identicon&r=PG",
            },
            {
                "id":
                3,
                "name":
                "image3",
                "image_url":
                "https://media.cntraveler.com/photos/57c0695b523900e805f2e31e/master/w_2048,h_1536,c_limit/table-mountain-cape-town-GettyImages-185108998.jpg",
            },
            {
                "id":
                4,
                "name":
                "image4",
                "image_url":
                "https://www.exoticca.com/uk/magazine/wp-content/uploads/2021/05/Avenue-of-Baobabs-BLOG.png",
            },
            {
                "id":
                5,
                "name":
                "image5",
                "image_url":
                "https://cdn.thecoolist.com/wp-content/uploads/2021/02/Most-beautiful-places-in-Africa.jpg",
            },
        ]
        return Response({
            "image": sample(images, 1)[0],
        })


class ValidateImage(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_image"]

    def post(self, request, *args, **kwargs):
        print(request.data)
        sleep(1)
        return Response({"message": "Image validated successfully"})


class GetAudiosToValidate(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]

    def get(self, request, *args, **kwargs):
        sleep(1)
        audios = [
            {
                "id": 6,
                "name": "image6",
                "image_url":
                "http://cdn.cnn.com/cnnnext/dam/assets/180508141319-03-amazing-places-africa---victoria-falls.jpg",
                "audio_url":
                "https://download.samplelib.com/mp3/sample-12s.mp3"
            },
            {
                "id": 1,
                "name": "image1",
                "image_url":
                "https://upload.wikimedia.org/wikipedia/commons/9/96/Pair_of_Merops_apiaster_feeding.jpg",
                "audio_url":
                "https://samplelib.com/lib/preview/mp3/sample-15s.mp3"
            },
            {
                "id": 2,
                "name": "image2",
                "image_url":
                "https://www.gravatar.com/avatar/e5ea2c87d14565ecfec13c3db67428a2?s=256&d=identicon&r=PG",
                "audio_url":
                "https://samplelib.com/lib/preview/mp3/sample-6s.mp3"
            },
        ]
        return Response({
            "audio": sample(audios, 1)[0],
        })


class ValidateAudio(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.validate_audio"]

    def post(self, request, *args, **kwargs):
        print(request.data, "validate audio")
        from time import sleep
        sleep(1)
        return Response({"message": "Image validated successfully"})


class SubmitTranscription(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.transcribe_audio"]

    def post(self, request, *args, **kwargs):
        print(request.data, "submit transcription")
        from time import sleep
        sleep(1)
        return Response({"message": "Image validated successfully"})


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
