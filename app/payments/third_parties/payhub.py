import requests
from django.conf import settings


class PayHub:

    def __init__(self):
        self.headers = {
            "Authorization": f"Token {settings.PAYHUB_SECRET_TOKEN}",
        }

    def collections(self, amount, mobile, network, transaction_id,
                    callback_url):
        data = {
            "amount": amount,
            "mobile_number": mobile,
            "network_code": network,
            "transaction_id": transaction_id,
            "wallet_id": settings.PAYHUB_WALLET_ID,
            "callback_url": callback_url,
        }
        return requests.post(
            "https://www.payhubghana.io/api/v1.0/debit_mobile_account/",
            data=data,
            headers=self.headers)

    def disbursement(self, amount, mobile, network, transaction_id,
                     callback_url):
        data = {
            "amount": amount,
            "mobile_number": mobile,
            "network_code": network,
            "transaction_id": transaction_id,
            "wallet_id": settings.PAYHUB_WALLET_ID,
            "callback_url": callback_url,
        }
        return requests.post(
            "https://www.payhubghana.io/api/v1.0/credit_mobile_account/",
            data=data,
            headers=self.headers)

    def status_check(self, transaction_id):
        return requests.get(
            f"https://www.payhubghana.io/api/v1.0/transaction_status?transaction_id={transaction_id}",
            headers=self.headers)

    def balance(self):
        return requests.get(
            f"https://www.payhubghana.io/api/v1.0/wallet_balance?wallet_id={settings.PAYHUB_WALLET_ID}",
            headers=self.headers)