from flask import Flask

from src.config import Settings
from src.controller import Controllers
from src.database.models.payfast import PayFastData, PayFastPay


class PayfastController(Controllers):

    def __init__(self):
        self.payfast_api_endpoint = "https://sandbox.payfast.co.za/eng/process?"
        self.payfast_data: PayFastData = PayFastData()
    def init_app(self,app:Flask, settings: Settings):
        self.payfast_data = PayFastData(
            merchant_id=settings.PAYFAST.SANDBOX_MERCHANT_ID,
            merchant_key=settings.PAYFAST.SANDBOX_MERCHANT_KEY
        )

    async def create_payment_request(self, payfast_payment: PayFastPay) -> str:

        self.payfast_data.return_url = payfast_payment.return_url
        self.payfast_data.cancel_url = payfast_payment.cancel_url
        self.payfast_data.notify_url = payfast_payment.notify_url
        self.payfast_data.item_name = payfast_payment.item_name
        self.payfast_data.item_description = payfast_payment.item_description
        self.payfast_data.amount = payfast_payment.amount
        self.payfast_data.uid = payfast_payment.uid
        self.payfast_data.company_id = payfast_payment.company_id
        self.payfast_data.subscription_id = payfast_payment.subscription_id

        data = self.payfast_data.dict()
        data.update(custom_str1=payfast_payment.subscription_id)
        data.update(custom_str2=payfast_payment.company_id)
        data.update(custom_str3=payfast_payment.uid)

        return self.payfast_api_endpoint + '&'.join([f'{key}={value}' for key, value in data.items()])

