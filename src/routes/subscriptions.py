import json

from flask import Blueprint, url_for, flash, redirect, request, render_template
from pydantic import ValidationError

from src.logger import init_logger
from src.authentication import admin_login
from src.database.models.companies import Company
from src.database.models.payments import Payment
from src.database.models.subscriptions import PlanNames, SubscriptionDetails, Subscriptions, TopUpPacks, Package
from src.database.models.users import User
from src.main import company_controller, paypal_controller, subscriptions_controller

subscriptions_route = Blueprint('subscriptions', __name__)

subscription_logger = init_logger(name="subscriptions_route_logger")


@subscriptions_route.get('/subscriptions/subscriptions')
@admin_login
async def get_subscriptions(user: User):
    """

    :param user:
    :return:
    """
    if not user.company_id:
        message: str = "You cannot subscribe please ensure to create a company"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('home.get_home'))
    context = dict(user=user)
    return render_template('billing/subscriptions.html', **context)


@subscriptions_route.post('/subscriptions/subscribe/<string:option>')
@admin_login
async def do_subscribe(user: User, option: str):
    """

    :param option:
    :param user:
    :return:
    """

    if option not in PlanNames.plan_names():
        message: str = "Please select a valid subscription plan"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))

    company_detail: Company = await company_controller.get_company_details(company_id=user.company_id)

    subscription_details: SubscriptionDetails = SubscriptionDetails().create_plan(plan_name=option.upper())
    subscription_logger.info(f"Created plan details: {subscription_details}")

    success_url: str = url_for('subscriptions.subscription_payment_successful')
    failure_url: str = url_for('subscriptions.subscription_payment_failure')

    payment, is_created = await paypal_controller.create_payment(payment_details=subscription_details, user=user,
                                                                 success_url=success_url, failure_url=failure_url)

    if is_created:
        # Redirect user to PayPal for payment approval
        subscription = Subscriptions(**subscription_details.dict(), company_id=user.company_id, payments=[])
        await subscriptions_controller.add_update_company_subscription(subscription=subscription)
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        flash(message=f"Error creating Payment : {payment.error}", category="danger")
        return redirect(url_for('company.get_admin'))


@subscriptions_route.get('/subscriptions/payment/success')
@admin_login
async def subscription_payment_successful(user: User):
    pass

    try:
        # Load JSON data
        _payload = request.json
        _signature = request.headers.get('Paypal-Transmission-Sig', None)
        if not _signature:
            return redirect(url_for('home.get_home'))

        request_valid = await paypal_controller.verify_signature(payload=_payload, signature=_signature)
        if not request_valid:
            return redirect(url_for('home.get_home'))

        data = request.json
        # Convert amount to float
    except json.JSONDecodeError as e:
        subscription_logger.error(str(e))
        return None

    # Extract payment amount
    amount = int(_payload.get("resource", {}).get("amount", {}).get("total"))

    subscription = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

    payment = Payment(subscription_id=subscription.subscription_id,
                      amount_paid=amount,
                      payment_method="paypal",
                      is_successful=True, month=1)

    payment = await subscriptions_controller.add_company_payment(payment=payment)
    subscription_logger.info("subscription payment succeeded")
    subscription_logger.info(payment)
    if amount < subscription.subscription_amount:
        flash(message=f"you have paid : {amount} instead of {subscription.subscription_amount}", category="danger")

    else:
        flash(message=f"Payment Of {amount} Made Successfully", category="success")

    return redirect(url_for('company.get_admin'))


@subscriptions_route.get('/subscriptions/payment/failure')
@admin_login
async def subscription_payment_failure():
    message: str = "Payment was not successful please try again later"
    flash(message=message, category="danger")
    subscription_logger.error(message)
    return redirect(url_for('company.get_admin'))


@subscriptions_route.post('/subscriptions/topup')
@admin_login
async def messaging_top_up(user: User):
    """

    :param user:
    :return:
    """
    if not user.company_id:
        message: str = "You cannot subscribe please ensure to create a company"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))

    try:
        top_up_pack = TopUpPacks(**request.form, company_id=user.company_id)
        subscription_logger.info(top_up_pack)

    except ValidationError as e:
        subscription_logger.error(f"Error On Subscriptions: {str(e)}")
        return redirect(url_for('company.get_admin'))

    company_detail: Company = await company_controller.get_company_details(company_id=user.company_id)
    if not company_detail:
        message: str = "You have no Valid Company Detail - please create a company"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))

    subscription: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

    if not subscription:
        message: str = "You have no Valid subscription - please create a company"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))

    if subscription.plan_name == PlanNames.FREE.value:
        message: str = "You cannot buy top up packages on a free plan -- please upgrade"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))

    top_up_package: Package = await subscriptions_controller.add_update_sms_email_package(top_up_pack=top_up_pack)

    success_url: str = url_for('subscriptions.package_payment_successful', package_id=top_up_package.package_id)
    failure_url: str = url_for('subscriptions.package_payment_failure', package_id=top_up_package.package_id)

    payment, is_created = await paypal_controller.create_payment(payment_details=top_up_pack, user=user,
                                                                 success_url=success_url, failure_url=failure_url)
    if is_created:
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)

    else:
        flash(message=f"Error creating Payment : {payment.error}", category="danger")
        return redirect(url_for('company.get_admin'))


@subscriptions_route.get('/subscriptions/package/success/<string:package_id>')
@admin_login
async def package_payment_successful(user: User, package_id: str):
    """

    :param user:
    :param package_id:
    :return:
    """
    _payload = request.json
    _signature = request.headers.get('Paypal-Transmission-Sig', None)
    if not _signature:
        return redirect(url_for('home.get_home'))

    request_valid = await paypal_controller.verify_signature(payload=_payload, signature=_signature)
    if not request_valid:
        return redirect(url_for('home.get_home'))

    # Extract payment amount
    amount = int(_payload.get("resource", {}).get("amount", {}).get("total"))

    _is_package_paid = await subscriptions_controller.set_package_to_paid(package_id=package_id)

    #
    if _is_package_paid:
        payment = Payment(package_id=package_id,
                          amount_paid=amount,
                          payment_method="paypal",
                          is_successful=True, month=1, comments="This is a payment for additional sms or email package")

        payment_ = await subscriptions_controller.add_company_payment(payment=payment)
        subscription_logger.info("payment for sms / email package succeeded")
        subscription_logger.info(payment)
        flash(message=f"Payment of {amount} for an SMS or Email Package was made successfully", category="success")

    return redirect(url_for('company.get_admin'))


@subscriptions_route.get('/subscriptions/package/failure/<string:package_id>')
@admin_login
async def package_payment_failure(user: User, package_id: str):
    """

    :param package_id:
    :param user:
    :return:
    """
    await subscriptions_controller.remove_package_its_unpaid(package_id=package_id)
    message: str = "Payment was not successfull please try again later"
    flash(message=message, category="danger")
    subscription_logger.error(message)
    return redirect(url_for('company.get_admin'))