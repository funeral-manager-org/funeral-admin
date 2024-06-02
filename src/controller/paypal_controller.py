import hashlib
import hmac

import requests
from flask import Flask
from paypalrestsdk import configure, Payment

from src.config import Settings
from src.controller import Controllers
from src.database.models.subscriptions import SubscriptionDetails
from src.database.models.users import User


class PayPalController(Controllers):
    def __init__(self):
        super().__init__()
        self.mode = "live"
        self._client_secret = ""

    def init_app(self, app: Flask, config_instance: Settings):
        self._client_secret = config_instance.PAYPAL_SETTINGS.SECRET_KEY
        configure({
            "mode": self.mode,
            "client_id": config_instance.PAYPAL_SETTINGS.CLIENT_ID,
            "client_secret": config_instance.PAYPAL_SETTINGS.SECRET_KEY
        })
        # self.api = Api(**{
        #     "mode": self.mode,
        #     "client_id": config_instance.PAYPAL_SETTINGS.CLIENT_ID,
        #     "client_secret": config_instance.PAYPAL_SETTINGS.SECRET_KEY
        # })
        super().init_app(app=app)

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get the exchange rate from one currency to another using an external API.

        :param from_currency: The source currency code.
        :param to_currency: The target currency code.
        :return: The exchange rate from the source currency to the target currency.
        """
        api_url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(api_url)
        data = response.json()
        return data["rates"][to_currency]

    def convert_to_usd(self, zar: int) -> int:
        """
        Convert ZAR (South African Rand) to USD (United States Dollar).

        :param zar: The amount in ZAR.
        :return: The equivalent amount in USD.
        """
        exchange_rate = self.get_exchange_rate("ZAR", "USD")
        self.logger.info(f"EXCHANGE RATE : {exchange_rate}")

        return int(round(zar * exchange_rate))

    async def create_payment(self, subscription_details: SubscriptionDetails, user: User,
                             success_url: str, failure_url: str) -> tuple[Payment, bool]:
        """
        :param subscription_details:
        :param failure_url:
        :param success_url:
        :param user:
        :return: A tuple containing the Payment object and a boolean indicating success or failure
        """
        total_amount = self.convert_to_usd(zar=subscription_details.subscription_amount)
        self.logger.info(f"Total Amount: {str(total_amount)}")
        # Include customer information and UID
        payment = Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": success_url,
                "cancel_url": failure_url
            },
            "transactions": [{
                "amount": {
                    "total": total_amount,
                    "currency": "USD"
                },
                "description": f"Funeral-Manager.org,  {subscription_details.plan_name} Subscription"
            }],
        })

        return payment, payment.create()

    async def verify_signature(self, payload: str, signature: str) -> bool:
        """

        :param payload:
        :param signature:
        :return:
        """
        expected_sig = hmac.new(
            bytes(self._client_secret, 'utf=8'),
            bytes(payload, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature)
