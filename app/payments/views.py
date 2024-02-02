import logging
from django.http import JsonResponse
from django.views import View
from payments.tasks import check_transaction_status

logger = logging.getLogger(__name__)


class PaymentCallbackView(View):
    def get(self, request):
        transaction_id = request.GET.get("transaction_id")

        logger.debug("Received callback for %s", transaction_id)

        check_transaction_status(transaction_id)
        return JsonResponse({"status": True})
