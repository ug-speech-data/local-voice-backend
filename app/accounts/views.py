from asyncio.log import logger

from accounts.models import Otp, User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from local_voice.utils.functions import get_errors_from_form


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = "on" in request.POST.get("remember_me", "")

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            if remember_me:
                request.session.set_expiry(86400 * 30)
            user.last_login_date = timezone.now()
            user.save()
            redirect_url = request.GET.get("next") or "dashboard:index"
            return redirect(redirect_url)
        else:
            context = {k: v for k, v in request.POST.items()}
            messages.warning(request, "Invalid credentials")
            return render(request, self.template_name, context)


class LogoutView(View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('accounts:login')


class ProfileView(View):
    template_name = 'accounts/profile.html'
    # form_class = UserUpdateForm

    @method_decorator(login_required(login_url="accounts:login"))
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    @method_decorator(login_required(login_url="accounts:login"))
    def post(self, request, *args, **kwargs):
        """For updating user profile"""
        user_groups = request.user.groups.all()
        request.user.groups.set(user_groups)
        if request.FILES.get("photo"):
            photo = request.FILES.get("photo")
            request.user.photo = photo
            request.user.save()
            messages.success(request, "Profile photo updated")
        else:
            form_class = self.form_class(request.POST, instance=request.user)
            if form_class.is_valid():
                user = form_class.save()
                # Prevent changing of verified phone numbers.
                if user.phone_verified():
                    user.phone = user.verified_phone
                    user.save()
                user.groups.set(user_groups)
                user.save()
                messages.success(request, "Profile updated")
            else:
                logger.error(form_class.errors)
                error = get_errors_from_form(form_class)
                messages.warning(request, error)
        return redirect("accounts:profile")


class ChangePasswordView(View):

    @method_decorator(login_required(login_url="accounts:login"))
    def post(self, request, *args, **kwargs):
        """For changing password"""
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, "Password changed")
            else:
                messages.warning(request, "Invalid old password")
        else:
            messages.warning(request, "Passwords do not match")
        return redirect("accounts:profile")


class VerifyPhoneView(View):
    template_name = 'accounts/verify_phone.html'

    def get(self, request):
        otp = Otp.objects.filter(
            address=request.user.phone).order_by("-created_at").first()
        if not otp or otp.expired():
            messages.warning(request, "No token found.")
            return redirect("dashboard:index")

        context = {
            "otp": otp,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pin = request.POST.get("pin")
        otp = Otp.objects.filter(
            address=request.user.phone).order_by("-created_at").first()
        if otp and otp.validate(pin):
            request.user.verified_phone = otp.address
            request.user.save()
            otp.delete()
            messages.success(request, "Phone number has been verified.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Invalid pin")
        return redirect(request.META.get("HTTP_REFERER"))


class SendOtp(View):

    def get(self, request):
        return redirect("dashboard:index")

    def post(self, request, *args, **kwargs):
        otp = Otp.objects.create(address=request.user.phone)
        otp.send_sms()
        return redirect("accounts:verify_phone")


class VerifyApplicationApprovalOTPView(View):
    """For verifying application approval OTP. The OTP was sent via ajax in ajax.py"""

    def get(self, request):
        return redirect("dashboard:index")

    def post(self, request):
        pin = request.POST.get("pin")
        model_name = request.POST.get("model_name")
        application_id = request.POST.get("application_id")
        model_class = get_application_model(model_name)

        if not model_class:
            messages.warning(request, "Invalid model")
            return redirect(request.META.get("HTTP_REFERER"))

        application = model_class.objects.filter(id=application_id).first()
        if not application:
            messages.warning(request, "Application not found.")
            return redirect(request.META.get("HTTP_REFERER"))

        otp = Otp.objects.filter(
            address=request.user.phone).order_by("-created_at").first()
        if otp and otp.validate(pin):
            application.otp_verification_date = timezone.now()
            application.save()
            otp.delete()
            messages.success(request, "OTP verified")
        else:
            messages.error(request, "Invalid pin")
        return redirect(request.META.get("HTTP_REFERER"))


class ResetPasswordSendOTPView(View):
    template_name = 'accounts/reset_password_send_otp.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        user = User.objects.filter(username=username).first()
        if not user:
            messages.warning(request, "User not found.")
            return redirect(request.META.get("HTTP_REFERER"))
        if not user.phone_verified():
            messages.warning(
                request,
                "Please your phone number was not verified. Kindly contact the administrator to reset your password."
            )
            return redirect(request.META.get("HTTP_REFERER"))

        Otp.objects.filter(address=user.phone).delete()
        otp = Otp.objects.create(address=user.phone)
        sent = otp.send_sms()
        if sent:
            return redirect("accounts:enter_otp", username, otp.id)
        else:
            messages.error(request, "Could not send OTP")
            return redirect(request.META.get("HTTP_REFERER"))


class EnterOTPToResetPasswordView(View):
    template_name = 'accounts/enter_otp.html'

    def get(self, request, username, otp_id):
        otp = Otp.objects.filter(id=otp_id).first()
        if not otp or otp.expired():
            messages.warning(request, "OTP not found.")
            return redirect("accounts:reset_password")
        context = {
            "otp": otp,
            "username": username,
        }
        return render(request, self.template_name, context)

    def post(self, request, username, otp_id):
        pin = request.POST.get("pin")
        otp = Otp.objects.filter(id=otp_id).order_by("-created_at").first()
        if not otp:
            messages.warning(request, "OTP not found.")
            return redirect("accounts:reset_password")

        if otp and otp.validate(pin):
            user = User.objects.filter(username=username).first()
            user.password_reset_verification_code = otp.pin
            user.save()
            otp.delete()
            return redirect("accounts:set_new_password", username, pin)
        else:
            messages.error(request, "Invalid pin.")
        return redirect("accounts:enter_otp", username, otp.id)


class SetNewPasswordsView(View):
    template_name = 'accounts/set_new_password.html'

    def get(self, request, username, verification_code):
        user = User.objects.filter(username=username).first()
        if not user:
            messages.warning(request, "User not found.")
            return redirect("accounts:reset_password")
        if user.password_reset_verification_code != verification_code:
            messages.warning(request, "Sorry, the link has expired.")
            return redirect("accounts:reset_password")

        return render(request, self.template_name)

    def post(self, request, username, verification_code):
        user = User.objects.filter(username=username).first()
        if not user:
            messages.warning(request, "User not found.")
            return redirect("accounts:reset_password")
        if user.password_reset_verification_code != verification_code:
            messages.warning(request, "Sorry, the link has expired.")
            return redirect("accounts:reset_password")

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("accounts:set_new_password", username,
                            verification_code)
        user.password_reset_verification_code = None
        user.set_password(password)
        user.save()
        messages.success(request, "Password has been reset.")
        return redirect("accounts:login")
