from django.urls import path

from . import views

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
]