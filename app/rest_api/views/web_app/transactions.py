import logging
from django.urls import reverse
from dashboard.models import Participant
from payments.tasks import bulk_check_transaction_status, update_participants_amount

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from accounts.models import User
from local_voice.utils.constants import (TransactionDirection,
                                         TransactionStatus,
                                         TransactionStatusMessages)
from payments.models import Transaction
from payments.third_parties.payhub import PayHub
from rest_api.permissions import APILevelPermissionCheck
from rest_api.serializers import PaymentUserSerializer, TransactionSerializer
from rest_api.views.mixins import SimpleCrudMixin

logger = logging.getLogger("app")
payhub = PayHub()


class GetPaymentUsers(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]
    serializer_class = PaymentUserSerializer

    model_class = User
    response_data_label = "user"
    response_data_label_plural = "users"

    def modify_response_data(self, users):
        return users.order_by("-wallet__balance")

    def post(self, *args, **kwargs):
        return Response({"detail": "Method not allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        return Response({"detail": "Method not allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TransactionHistory(SimpleCrudMixin):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]
    serializer_class = TransactionSerializer

    model_class = Transaction
    response_data_label = "transaction"
    response_data_label_plural = "transactions"

    def post(self, *args, **kwargs):
        return Response({"detail": "Method not allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        return Response({"detail": "Method not allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TransactionStatusCheck(generics.GenericAPIView):
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids")
        bulk_check_transaction_status.delay(ids)
        return Response({
            "message":
            f"Checking status of {len(ids)} transactions"
        })


class CreditUsers(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, **kwargs):
        user_ids = request.data.get("ids")
        amount = request.data.get("amount")
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            wallet = user.wallet
            transaction = Transaction.objects.create(
                amount=amount,
                wallet=wallet,
                fullname=user.fullname,
                initiated_by=request.user,
                status=TransactionStatus.SUCCESS.value,
                direction=TransactionDirection.IN.value,
                status_message=TransactionStatusMessages.SUCCESS.value,
                note="DIRECT DEPOSIT")

            transaction.update_wallet_balances()
        return Response(
            {"message": f"Credited wallets of {users.count()} users."})


class PayUsers(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, **kwargs):
        user_ids = request.data.get("ids", [])
        amount = request.data.get("amount")
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            wallet = user.wallet
            transaction = Transaction.objects.create(
                amount=amount,
                wallet=wallet,
                fullname=user.fullname,
                phone_number=user.phone,
                network=user.phone_network,
                initiated_by=request.user,
                direction=TransactionDirection.OUT.value,
                note="PAYOUT")

            # Make API calls
            transaction.execute()

        return Response({
            "message":
            f"Initiated payment request for {users.count()} users."
        })


class PayValidationBenefit(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, **kwargs):
        user_ids = request.data.get("ids")
        users = User.objects.filter(id__in=user_ids)
        callback_url = request.build_absolute_uri(reverse("payments:callback"))
        for user in users:
            wallet = user.wallet
            amount = min(wallet.validation_benefit, wallet.balance)
            if amount <= 0 or Transaction.objects.filter(
                    wallet=wallet,
                    status=TransactionStatus.PENDING.value).exists():
                continue
            transaction = Transaction.objects.create(
                amount=amount,
                wallet=wallet,
                fullname=user.fullname,
                phone_number=user.phone,
                network=user.phone_network,
                initiated_by=request.user,
                direction=TransactionDirection.OUT.value,
                note="VALIDATION_PAYOUT")

            # Make API calls
            transaction.execute(callback_url)

        return Response({
            "message":
            f"Initiated payment request for {users.count()} users."
        })


class PayUsersBalance(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, APILevelPermissionCheck]
    required_permissions = ["setup.manage_payment"]

    def post(self, request, **kwargs):
        user_ids = request.data.get("ids")
        users = User.objects.filter(id__in=user_ids)
        callback_url = request.build_absolute_uri(reverse("payments:callback"))
        for user in users:
            wallet = user.wallet
            amount = wallet.balance
            if amount <= 0 or Transaction.objects.filter(
                    wallet=wallet,
                    status=TransactionStatus.PENDING.value).exists():
                continue
            transaction = Transaction.objects.create(
                amount=amount,
                wallet=wallet,
                fullname=user.fullname,
                phone_number=user.phone,
                network=user.phone_network,
                initiated_by=request.user,
                direction=TransactionDirection.OUT.value,
                note="PAYOUT")

            # Make API calls
            transaction.execute(callback_url)

        return Response({
            "message":
            f"Initiated payment request for {users.count()} users."
        })


class GetPayHubBalance(generics.GenericAPIView):
    required_permissions = ["setup.manage_payment"]

    def get(self, request, *args, **kwargs):
        balance = "--"
        try:
            response = payhub.balance()
            if response.status_code == 200:
                balance = response.json().get("available_balance")
        except Exception as e:
            logger.error(e)
            balance = "Error"
        return Response({"balance": str(balance)})


class PayUnregisteredUsers(generics.GenericAPIView):
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        amount = request.data.get("amount")
        fullname = request.data.get("fullname")
        momo_number = request.data.get("momo_number")
        network = request.data.get("network")
        note = request.data.get("note")
        callback_url = request.build_absolute_uri(reverse("payments:callback"))

        transaction = Transaction.objects.create(
            amount=amount,
            fullname=fullname,
            phone_number=momo_number,
            network=network,
            initiated_by=request.user,
            direction=TransactionDirection.OUT.value,
            note=note)

        # Make API calls
        transaction.execute(callback_url)

        return Response({"message": "Initiated payment successfully."})


class RecalculateParticipantAmount(generics.GenericAPIView):
    required_permissions = ["setup.manage_payment"]

    def post(self, request, *args, **kwargs):
        participants = Participant.objects.filter(
            excluded_from_payment=False, flatten=False)
        update_participants_amount.delay(filterUnpaid=False)
        return Response({"message": f"Initiated recalcuation for {participants.count()} successfully."})
