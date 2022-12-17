from django.urls import path

from . import views

app_name = "setup"

#yapf: disable
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("rank/change", views.CreateUpdateRank.as_view(), name="change_rank"),
    path("rank/delete", views.DeleteRank.as_view(), name="delete_rank"),
    path("document-type/change", views.CreateUpdateApplicationDocumentType.as_view(),name="change_document_type"),
    path("document-type/delete", views.DeleteApplicationDocumentType.as_view(), name="delete_document_type"),
    path("role/change", views.CreateUpdateGroup.as_view(), name="change_role"),
    path("role/delete", views.DeleteGroup.as_view(), name="delete_role"),
    path("user/delete", views.DeleteUser.as_view(), name="delete_user"),
    path("role/<int:role_id>/manage/", views.RoleManagementView.as_view(), name="manage_role"),
    path("user/change", views.CreateUpdateUser.as_view(), name="change_user"),
    path("retirement-reason/change", views.CreateUpdateRetirementReason.as_view(), name="change_retirement_reason"),
    path("retirement-reason/delete", views.DeleteRetirementReason.as_view(), name="delete_retirement_reason"),
    path("reviewer/change", views.CreateUpdateReviewer.as_view(), name="change_reviewer"),
    path("reviewer/delete", views.DeleteReviewer.as_view(), name="delete_reviewer"),

    path("sms-template/create-update", views.CreateUpdateSmsTemplateView.as_view(), name="create_update_sms_template"),
    path("sms-template/delete", views.DeleteSmsTemplate.as_view(), name="delete_sms_template"),



    path("relationship/change", views.CreateUpdateRelationship.as_view(), name="change_relationship"),
    path("relationship/delete", views.DeleteRelationship.as_view(), name="delete_relationship"),

    path("update-sysconfig", views.UpdateSysConfigView.as_view(), name="update_sysconfig"),

    path("help", views.HelpView.as_view(), name="help"),
]
