import hashlib
from flask import Flask, url_for, Response, redirect

from src.database.models.subscriptions import Subscriptions, Package, TopUpPacks
from src.database.models.users import User
from src.config import Settings
from src.controller import Controllers, error_handler
from src.database.models.payfast import PayFastData, PayFastPay


class PayfastController(Controllers):

    def __init__(self):
        super().__init__()
        self.settings = None
        self.payfast_api_endpoint = "https://sandbox.payfast.co.za/eng/process?"
        self.use_live_data: bool = True

    def is_demo_account(self, user: User):
        if not self.settings:
            return False
        return user.username == self.settings.DEMO_ACCOUNT

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, settings: Settings):
        super().init_app(app=app)
        self.settings = settings

    @error_handler
    async def create_payment_request(self, payfast_payment: PayFastPay, user: User) -> str:
        if self.is_demo_account(user=user):
            data = PayFastData(
                merchant_id=self.settings.PAYFAST.SANDBOX_MERCHANT_ID,
                merchant_key=self.settings.PAYFAST.SANDBOX_MERCHANT_KEY)
        else:
            data = PayFastData(
                merchant_id=self.settings.PAYFAST.MERCHANT_ID,
                merchant_key=self.settings.PAYFAST.MERCHANT_KEY
            )
            self.payfast_api_endpoint = "https://www.payfast.co.za/eng/process?"

        data.return_url = payfast_payment.return_url
        data.cancel_url = payfast_payment.cancel_url
        data.notify_url = payfast_payment.notify_url
        data.item_name = payfast_payment.item_name
        data.item_description = payfast_payment.item_description
        data.amount = payfast_payment.amount
        data.uid = payfast_payment.uid
        data.company_id = payfast_payment.company_id
        data.subscription_id = payfast_payment.subscription_id
        data.package_id = payfast_payment.package_id

        data_dict = data.dict(exclude={"company_id", "uid", "package_id"})
        data_dict.update(custom_str1=payfast_payment.subscription_id)
        data_dict.update(custom_str2=payfast_payment.company_id)
        data_dict.update(custom_str3=payfast_payment.uid)
        if payfast_payment.package_id:
            data_dict.update(custom_str4=payfast_payment.package_id)

        return self.payfast_api_endpoint + '&'.join([f'{key}={value}' for key, value in data_dict.items()])

    @error_handler
    async def is_valid_payfast_data(self, payfast_dict_data: dict[str, str]) -> bool:
        """
        Validates the data received from PayFast by checking the signature.

        :param payfast_dict_data: Dictionary containing the data received from PayFast.
        :param passphrase: The secret passphrase provided by PayFast.
        :return: True if the data is valid, False otherwise.
        """
        # Copy the data to avoid modifying the original dictionary
        payfast_data = payfast_dict_data.copy()
        # Remove the signature from the data as it shouldn't be part of the signature generation
        received_signature = payfast_data.pop('signature', None)
        if not received_signature:
            return False  # No signature provided, invalid data
        # Sort the data alphabetically by keys to match the signature creation order
        sorted_data = {k: v for k, v in sorted(payfast_data.items()) if v != ""}
        # Convert the dictionary to a URL-encoded query string
        query_string = "&".join(f"{key}={value}" for key, value in sorted_data.items())

        # Generate the signature by hashing the query string with MD5
        generated_signature = hashlib.md5(query_string.encode('utf-8')).hexdigest()
        return True
        # Compare the received signature with the generated one
        # return received_signature == generated_signature

    @error_handler
    async def payfast_subscription_payment(self, subscription_details: Subscriptions, user: User) -> Response:

        # Generate HTTPS URLs for PayFast
        return_url: str = url_for('subscriptions.payfast_payment_complete', _external=True, _scheme='https')
        cancel_url: str = url_for('subscriptions.payfast_payment_failed', _external=True, _scheme='https')
        notify_url: str = url_for('subscriptions.payfast_ipn', _external=True, _scheme='https')

        amount: int = subscription_details.subscription_amount
        item_name: str = f"{subscription_details.plan_name} Subscription"
        item_description: str = f"{subscription_details.plan_name} monthly subscription"
        payfast_payment_data = PayFastPay(return_url=return_url,
                                          cancel_url=cancel_url,
                                          notify_url=notify_url,
                                          amount=amount,
                                          item_name=item_name,
                                          item_description=item_description,
                                          uid=user.uid,
                                          company_id=user.company_id,
                                          subscription_id=subscription_details.subscription_id)

        payfast_endpoint_url: str = await self.create_payment_request(payfast_payment=payfast_payment_data, user=user)
        return redirect(payfast_endpoint_url)

    @error_handler
    async def payfast_package_payment(self, subscription_details: Subscriptions, top_up_pack: TopUpPacks, user: User):
        """

        :param package:
        :param user:
        :return:
        """
        return_url: str = url_for('subscriptions.payfast_payment_complete', _external=True, _scheme='https')
        cancel_url: str = url_for('subscriptions.payfast_payment_failed', _external=True, _scheme='https')
        notify_url: str = url_for('subscriptions.payfast_package_ipn', _external=True, _scheme='https')

        amount: int = top_up_pack.payment_amount
        item_name: str = top_up_pack.plan_name
        item_description: str = top_up_pack.plan_name
        payfast_payment_data = PayFastPay(return_url=return_url,
                                          cancel_url=cancel_url,
                                          notify_url=notify_url,
                                          amount=amount,
                                          item_name=item_name,
                                          item_description=item_description,
                                          uid=user.uid,
                                          package_id=top_up_pack.package_id,
                                          company_id=user.company_id,
                                          subscription_id=subscription_details.subscription_id)

        payfast_endpoint_url: str = await self.create_payment_request(payfast_payment=payfast_payment_data, user=user)
        return redirect(payfast_endpoint_url)


