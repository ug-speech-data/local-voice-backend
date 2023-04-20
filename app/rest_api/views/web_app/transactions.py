import logging

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
        transactions = Transaction.objects.filter(id__in=ids)
        for transaction in transactions:
            transaction.recheck_status()
        return Response({
            "message":
            f"Checking status of {transactions.count()} transactions"
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
        for user in users:
            wallet = user.wallet
            amount = min(wallet.validation_benefit, wallet.balance)
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
            transaction.execute()

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
        for user in users:
            wallet = user.wallet
            amount = wallet.balance
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
