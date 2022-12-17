from django.urls import path

from . import views

app_name = "accounts"

# yapf: disable
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("set-new-password/<str:username>/<str:verification_code>", views.SetNewPasswordsView.as_view(), name="set_new_password"),
    path("reset-password/", views.ResetPasswordSendOTPView.as_view(), name="reset_password"),
    path("enter-otp/<str:username>/<str:otp_id>", views.EnterOTPToResetPasswordView.as_view(), name="enter_otp"),

    path("verify-phone", views.VerifyPhoneView.as_view(), name="verify_phone"),
    path("send-otp", views.SendOtp.as_view(), name="send_otp"),
]
