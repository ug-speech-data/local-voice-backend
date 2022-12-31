from django.urls import path

from . import views

# yapf: disable
urlpatterns = [
    path("auth/register/", views.UserRegistrationAPI.as_view()),
    path("auth/change_password/", views.UserChangePassword.as_view()),
    path("auth/login/", views.UserLoginAPI.as_view()),
    path("auth/logout/", views.UserLogoutAPI.as_view()),
    path("auth/profile/", views.MyProfile.as_view()),
    path("participants/", views.CreateParticipantAPI.as_view()),
    path("get-mobile-app-configurations/", views.MobileAppConfigurationAPI.as_view()),
    path("get-assigned-images/", views.GetAssignedImagesAPI.as_view()),
    path("upload-audio/", views.UploadAudioAPI.as_view()),
    path("auth/user-permissions/", views.MyPermissions.as_view()),
    path("auth/logout/", views.LogoutApiView.as_view()),
]

urlpatterns += [
    path("get-image-to-validate", views.GetImagesToValidate.as_view()),
    path("get-audio-to-validate", views.GetAudiosToValidate.as_view()),
    path("validate-image/", views.ValidateImage.as_view()),
    path("validate-audio/", views.ValidateAudio.as_view()),
    path("submit-transcription/", views.SubmitTranscription.as_view()),

    path("categories/", views.CategoriesAPI.as_view()),
    path("groups/", views.GroupsAPI.as_view()),
    path("permissions/group/<int:group_id>/", views.PermissionsAPI.as_view()),
    path("users/", views.UsersAPI.as_view()),
    path("configurations/", views.AppConfigurationAPI.as_view()),

    path("images/", views.UploadedImagesAPI.as_view()),
]
