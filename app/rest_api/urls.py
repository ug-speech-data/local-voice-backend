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
    path("get-mobile-app-configurations/",
         views.MobileAppConfigurationAPI.as_view()),
    path("get-assigned-images/", views.GetAssignedImagesAPI.as_view()),
#     path("upload-audio/", views.UploadAudioAPI.as_view()),
    path("auth/user-permissions/", views.MyPermissions.as_view()),
    path("auth/logout/", views.LogoutApiView.as_view()),
    path("search-users", views.SearchUser.as_view()),
    path("archive-user/", views.ArchiveUser.as_view()),
    path("user-statistics/", views.GetUserStatistics.as_view()),
]

urlpatterns += [
    path("get-image-to-validate", views.GetImagesToValidate.as_view()),
    path("get-audio-to-validate", views.GetAudiosToValidate.as_view()),
    path("get-audio-to-transcribe", views.GetAudiosToTranscribe.as_view()),
    path("get-transcription-to-validate",
         views.GetTranscriptionToValidate.as_view()),
    path("get-transcription-to-resolve/",
         views.GetAudioTranscriptionToResolve.as_view()),

    path("validate-image/", views.ValidateImage.as_view()),
    path("validate-audio/", views.ValidateAudio.as_view()),
    path("submit-transcription/", views.SubmitTranscription.as_view()),
    path("validate-transcription/",
         views.ValidateTranscription.as_view()),  # deprecated

    path("categories/", views.CategoriesAPI.as_view()),
    path("groups/", views.GroupsAPI.as_view()),
    path("permissions/group/<int:group_id>/", views.PermissionsAPI.as_view()),
    path("users/", views.UsersAPI.as_view()),
    path("configurations/", views.AppConfigurationAPI.as_view()),

    path("collected-images/", views.CollectedImagesAPI.as_view()),
    path("collected-audios/", views.CollectedAudiosAPI.as_view()),
    path("collected-transcriptions/", views.CollectedTranscriptionsAPI.as_view()),
    path("collected-participants/", views.CollectedParticipantsAPI.as_view()),

    path("reshuffle-images/", views.ReShuffleImageIntoBatches.as_view()),
    path("assign-images-batch-to-user/",
         views.AssignImageBatchToUsers.as_view()),

    path("export-audio-data/", views.ExportAudioData.as_view()),
    path("notifications/", views.NotificationAPI.as_view()),

    path("image-preview-navigation", views.ImagePreviewNavigation.as_view()),
    path("dashboard-statistics/", views.GetDashboardStatistics.as_view()),

    path("get-enumerators/", views.GetEnumerators.as_view()),
    path("get-uploaded-audios/", views.GetUploadedAudios.as_view()),
    path("limited-users/", views.LimitedUsersAPIView.as_view()),

    path("get-assigned-audios-to-validate/",
         views.GetBulkAssignedToValidate.as_view()),
    path("get-assigned-audios-to-transcribe/",
         views.GetBulkAssignedToTranscribe.as_view()),
    path("get-assigned-transcriptions-to-resolve/",
         views.GetBulkAssignedTranscriptionsToResolve.as_view()),
]


urlpatterns += [
    path("submit-crawler-images/", views.SubmitCrawlerImages.as_view()),
    path("web-app-configurations/", views.WebAppConfigurations.as_view()),
]

# Bulk Actions
urlpatterns += [
    path("participants-bulk-actions/", views.ParticipantsBulkAction.as_view()),
    path("images-bulk-actions/", views.ImagesBulkAction.as_view()),
    path("audios-bulk-actions/", views.AudiosBulkAction.as_view()),
    path("transcriptions-bulk-actions/",
         views.TranscriptionsBulkAction.as_view()),
]

# Payment
urlpatterns += [
    path("payments/users", views.GetPaymentUsers.as_view()),
    path("payments/credit-users/", views.CreditUsers.as_view()),
    path("payments/pay-users/", views.PayUsers.as_view()),
    path("payments/pay-users-validation-benefit/",
         views.PayValidationBenefit.as_view()),
    path("payments/pay-users-balance/", views.PayUsersBalance.as_view()),
    path("payments/transactions-history", views.TransactionHistory.as_view()),
    path("payments/transactions-status-check",
         views.TransactionStatusCheck.as_view()),
    path("payments/balance", views.GetPayHubBalance.as_view()),
    path("payments/pay-ungresiter-user/", views.PayUnregisteredUsers.as_view()),
]
