import datetime

from flask import Blueprint, render_template, url_for, redirect, flash, request

from src.authentication import admin_login
from src.database.models.payments import Payment
from src.database.models.subscriptions import Subscriptions, SubscriptionDetails
from src.database.models.users import User
from src.logger import init_logger
from src.main import subscriptions_controller, paypal_controller

billing_route = Blueprint('billing', __name__)
billing_logger = init_logger('billing_logger')


@billing_route.get('/admin/billing')
@admin_login
async def get_billing(user: User):
    """

    :param user:
    :return:
    """

    subscription: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)
    if not subscription:
        subscription = {}
    billing_logger.info(f"{subscription}")
    plan_details: SubscriptionDetails = await subscriptions_controller.return_plan_details(plan_name=subscription.plan_name)
    context = dict(user=user, subscription_account=subscription, plan_details=plan_details)
    return render_template('billing/billing.html', **context)

@billing_route.get('/admin/billing/tax-invoice/<string:transaction_id>')
@admin_login
async def print_subscription_payment_tax_invoice(user: User, transaction_id: str):
    """

        print_subscription_payment_tax_invoice
    """
    payment: Payment = await subscriptions_controller.get_company_subscription_payment(transaction_id=transaction_id)
    if not isinstance(payment, Payment):
        message="Unable to find the invoice"
        flash(message=message,category="danger")
        return redirect(url_for('billing.get_billing'))

    subscription_account: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)
    if subscription_account.subscription_id != payment.subscription_id:
        message="You changed your subscription since making this payment can no longer reprint your invoice"
        flash(message=message,category="danger")
        return redirect(url_for('billing.get_billing'))

    generated_on = datetime.datetime.now()
    context = dict(user=user, subscription_account=subscription_account, payment=payment, generated_on=generated_on)

    if payment.package_id:
        package = await subscriptions_controller.get_package(package_id=payment.package_id)
        context.update(package=package)

    return render_template('receipts/system/subscription_payment.html', **context)

@billing_route.post('/admin/billing/paynow')
@admin_login
async def do_pay_now(user: User):
    """
        this will pay the monthly payment as stipulated on billing
    :param user:
    :return:
    """
    # company_detail: Company = await company_controller.get_company_details(company_id=user.company_id)
    subscription: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

    success_url: str = url_for('billing.payment_successful', _external=True, _scheme='https')
    failure_url: str = url_for('billing.payment_failure', _external=True, _scheme='https')

    payment, is_created = await paypal_controller.create_payment(payment_details=subscription,
                                                                 user=user,
                                                                 success_url=success_url, failure_url=failure_url)
    if is_created:
        # Redirect user to PayPal for payment approval
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        flash(message=f"Error creating Payment : {payment.error}", category="danger")
        return redirect(url_for('company.get_admin'))


@billing_route.get('/admin/billing/payment-successfull')
@admin_login
async def payment_successful(user: User):
    """

    :param user:
    :return:
    """
    _payload = request.json
    _signature = request.headers.get('Paypal-Transmission-Sig', None)
    if not _signature:
        return redirect(url_for('home.get_home'))

    request_valid = await paypal_controller.verify_signature(payload=_payload, signature=_signature)
    if not request_valid:
        return redirect(url_for('home.get_home'))

    data = request.json

    amount = int(_payload.get("resource", {}).get("amount", {}).get("total"))
    subscription = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

    payment = Payment(subscription_id=subscription.subscription_id,
                      amount_paid=amount,
                      payment_method="paypal",
                      is_successful=True, month=1)

    payment = await subscriptions_controller.add_company_payment(payment=payment)
    billing_logger.info("subscription payment succeeded")
    billing_logger.info(payment)
    if amount < subscription.subscription_amount:
        flash(message=f"you have paid : {amount} instead of {subscription.subscription_amount}", category="danger")

    else:
        flash(message=f"Payment Of {amount} Made Successfully", category="success")

    return redirect(url_for('company.get_admin'))


@billing_route.get('/admin/billing/payment-failed')
@admin_login
async def payment_failure(user: User):
    """

    :param user:
    :return:
    """
    message: str = "Payment was not successful please try again later"
    billing_logger.error(message)

    flash(message=message, category="danger")
    return redirect(url_for('company.get_admin'))
