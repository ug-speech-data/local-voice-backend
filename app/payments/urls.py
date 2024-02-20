from django.urls import path

from . import views

# yapf: disable
app_name = "payments"

urlpatterns = [
    path("callback/", views.PaymentCallbackView.as_view(), name="callback"),
]
