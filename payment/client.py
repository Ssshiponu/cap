import requests
import json
from django.conf import settings
from .models import BkashTransaction

class BkashClient:
    def __init__(self):
        self.config = settings.BKASH

    def get_token(self):
        """
        Call bKash to get an access token.
        """
        url = self.config["TOKEN_GRANT_URL"]
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "app_key": self.config["APP_KEY"],
            "app_secret": self.config["APP_SECRET"]
        }
        resp = requests.post(url, headers=headers, json=body)
        data = resp.json()
        # handle error etc.
        return data  # e.g. {"id_token": "...", "expires_in": ...}

    def create_payment(self, order_id: str, amount: float, token: str, **extra):
        """
        Create a payment with bKash.
        """
        url = self.config["CREATE_URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
        }
        body = {
            "mode": "0011",  # depends on your integration mode
            "amount": f"{amount:.2f}",
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": order_id,
            # other fields (billingAddress, etc.) optional
        }
        body.update(extra)
        resp = requests.post(url, headers=headers, json=body)
        return resp.json()

    def execute_payment(self, payment_id: str, token: str):
        """
        After create, execute the payment (user approval).
        """
        url = self.config["EXECUTE_URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
        }
        body = {
            "paymentID": payment_id
        }
        resp = requests.post(url, headers=headers, json=body)
        return resp.json()

    def query_payment(self, payment_id: str, token: str):
        """
        Query payment status.
        """
        url = self.config["QUERY_URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
        }
        body = {"paymentID": payment_id}
        resp = requests.post(url, headers=headers, json=body)
        return resp.json()
