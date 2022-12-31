from random import sample
from time import sleep

from django.contrib.auth.models import Group, Permission
from rest_framework import generics, permissions
from rest_framework.response import Response

from accounts.forms import GroupForm, UserForm
from accounts.models import User
from dashboard.forms import CategoryForm
from dashboard.models import Category, Image
from local_voice.utils.functions import (get_errors_from_form,
                                         relevant_permission_objects)
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import (AppConfigurationSerializer,
                                  CategorySerializer,
                                  GroupPermissionSerializer, GroupSerializer,
                                  ImageSerializer, UserSerializer)
from rest_api.views.mixins import SimpleCrudMixin
from setup.models import AppConfiguration


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


class UploadedImagesAPI(SimpleCrudMixin):
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
            image_obj.validations.all().delete()
            image_obj.categories.clear()
        image_obj.save()

        return Response({
            "message":
            "Image uploaded successfully",
            self.response_data_label:
            self.serializer_class(image_obj, context={
                "request": request
            }).data
        })
