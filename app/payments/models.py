from django.db import models
import logging
from local_voice.utils.constants import TransactionStatus
from local_voice.utils.constants import TransactionDirection
from django.db import transaction as django_db_transaction
from django.utils.decorators import method_decorator
from django.utils import timezone

logger = logging.getLogger("app")

#yapf: disable

class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ("new", "New"),
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]
    TRANSACTION_DIRECTION = [
        (TransactionDirection.IN.value,TransactionDirection.IN.value),
        (TransactionDirection.OUT.value,TransactionDirection.OUT.value),
    ]
    def generate_id():
        return timezone.now().strftime("%y%m%d%H%M%S%f")

    transaction_id = models.CharField(max_length=20,unique=True, default=generate_id)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet = models.ForeignKey("accounts.Wallet",on_delete=models.SET_NULL,null=True,blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    network = models.CharField(max_length=255, blank=True, null=True)
    fullname = models.CharField(max_length=255, blank=True, null=True)
    response_data = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    initiated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=TRANSACTION_DIRECTION)
    status = models.CharField(max_length=255, blank=True, null=True, choices=TRANSACTION_STATUS, default="new")
    status_message = models.CharField(max_length=255, blank=True, null=True)
    wallet_balances_updated = models.BooleanField(default=False)
    accepted_by_provider = models.BooleanField(default=False)


    class Meta:
        db_table = "transactions"

    def __str__(self):
        return self.transaction_id

    def success(self):
        return self.status == TransactionStatus.SUCCESS.value


    def execute(self, callback_url=None):
        """Execute this transaction by making the actual API calls and updating the status, amount, wallets, etc.
        This method is idempotent.
        """
        from payments.tasks import execute_transaction  # Avoid circular imports
        return execute_transaction.delay(self.transaction_id, callback_url)

    def retry(self):
        """Retry this transaction in the case of failure. This method is idempotent."""
        if self.success():
            logger.info(
                f"Transaction {self.transaction_id} is already successful")
            return
        if not self.accepted_by_provider:
            # This transaction has not been executed yet.
            self.execute()
        else:
            # This transaction has been executed, recheck the status in the provider's system.
            self.recheck_status()

    def recheck_status(self):
        """This method updates the status of this transaction.
        As well as performing other idempotent actions related to the transactions.
        i.e., crediting stores, updating wallets, etc. supposed they've not been done already.
        """
        from payments.tasks import check_transaction_status  # Avoid circular imports
        if self.accepted_by_provider:
            check_transaction_status.delay(self.transaction_id)


    @method_decorator(django_db_transaction.atomic())
    def update_wallet_balances(self):
        if not self.wallet:
            logger.info(f"Transaction {self.transaction_id} does not have wallet.")
            return

        if not self.success():
            logger.info(f"Transaction {self.transaction_id} is not successful")
            return

        if self.wallet_balances_updated:
            logger.info(
                f"Transaction {self.transaction_id} wallet balances are already updated"
            )
            return

        if self.direction == TransactionDirection.IN.value:
            self.wallet.credit_wallet(self.amount)

        if self.direction == TransactionDirection.OUT.value:
            self.wallet.increase_payout_amount(self.amount)

        self.wallet_balances_updated = True
        self.paid = True
        self.save()
        return True