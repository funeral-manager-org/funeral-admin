import json
from typing import Dict
from flask import Blueprint, url_for, flash, redirect, request, render_template, jsonify
from pydantic import ValidationError
from src.authentication import admin_login
from src.database.models.companies import Company
from src.database.models.payments import Payment
from src.database.models.subscriptions import PlanNames, SubscriptionDetails, Subscriptions, TopUpPacks, Package
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, paypal_controller, subscriptions_controller, payfast_controller

subscriptions_route = Blueprint('subscriptions', __name__)

subscription_logger = init_logger(name="subscriptions_route_logger")


@subscriptions_route.post('/_ipn/payfast')
async def payfast_ipn():
    # Convert the incoming form data to a dictionary
    payfast_dict_data: Dict[str, str] = request.form.to_dict()
    subscription_logger.info(f"Incoming Payment Notification: {payfast_dict_data}")

    # Validate the received data
    if await payfast_controller.is_valid_payfast_data(payfast_dict_data=payfast_dict_data):
        # Extracting relevant fields from the data
        payment_status = payfast_dict_data.get('payment_status')
        amount_gross = payfast_dict_data.get('amount_gross')
        pf_payment_id = payfast_dict_data.get('pf_payment_id')
        item_name = payfast_dict_data.get('item_name')
        email_address = payfast_dict_data.get('email_address')
        merchant_id = payfast_dict_data.get('merchant_id')
        # TODO - send payment receipt and notice welcoming the client to our services
        # Parsing the item_name to get plan_name and payment_type
        plan_name, payment_type = item_name.split(" ")

        # Custom fields which might not be present
        subscription_id = payfast_dict_data.get("custom_str1")
        company_id = payfast_dict_data.get("custom_str2")
        uid = payfast_dict_data.get("custom_str3")
        subscription_logger.info(f"Verified Request Data For ITN of company: {company_id} ")

        if payment_status == "COMPLETE" and payment_type.casefold() == "subscription":
            # Fetch the subscription details based on company_id
            subscription = await subscriptions_controller.get_company_subscription(company_id=company_id)
            subscription_logger.info(f"Able to Retrive the Company Subsciption: {subscription}")
            if isinstance(subscription, Subscriptions):
                # Create a Payment record for the subscription
                try:
                    payment = Payment(
                        subscription_id=subscription.subscription_id,
                        amount_paid=amount_gross,
                        payment_method="payfast",
                        is_successful=True,
                        month=1,  # Assuming the payment covers 1 month, adjust if needed
                        comments=f"payfast payment for company : {company_id}"
                    )
                    subscription_logger.info(f"Created Payment Type : {payment}")

                    # Store the payment in the database
                    payment_data: Payment = await subscriptions_controller.add_company_payment(payment=payment)
                    subscription_logger.info(f"Payment Record Created: {payment_data}")
                    # Return a success response
                    return jsonify(
                        dict(message=f"Successfully paid for {plan_name} subscription", data=payfast_dict_data)), 200
                except ValidationError as e:
                    subscription_logger.warning(str(e))

            else:
                subscription_logger.warning(f"Could not Verify if subscription is of the type Subscrtiption")

            subscription_logger.warning(f"Payment not complete or not a subscription: {payfast_dict_data}")
            return jsonify(dict(message="Payment not complete or invalid payment type", data=payfast_dict_data)), 400

        else:
            # Log the issue or handle failed payment status
            subscription_logger.warning(f"Payment not complete or not a subscription: {payfast_dict_data}")
            return jsonify(dict(message="Payment not complete or invalid payment type", data=payfast_dict_data)), 400
    else:
        # Handle invalid data, possibly log and alert
        subscription_logger.warning(f"Invalid PayFast data received: {payfast_dict_data}")
        return jsonify(dict(message="Invalid data received", data=payfast_dict_data)), 400


@subscriptions_route.get('/subscriptions/payfast-success')
@admin_login
async def payfast_payment_complete(user: User):
    """
    payfast_payment_complete
        guru
        :param user:
        :return:
    """
    flash(message="Payment completed successfully", category="success")
    return redirect(url_for('company.get_admin'))
@subscriptions_route.get('/subscriptions/payfast-failure')
@admin_login
async def payfast_payment_failed(user: User):
    """

    :param user:
    :return:
    """
    flash(message="Payment was cancelled please try again later", category="danger")
    return redirect(url_for('company.get_admin'))


@subscriptions_route.get('/subscriptions/subscriptions')
@admin_login
async def get_subscriptions(user: User):
    """
        **get_subscriptions**
    :param user:
    :return:
    """
    if not user.company_id:
        message: str = "You cannot subscribe please ensure to create a company"
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('home.get_home'))

    subscription_account: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)
    subscription_plans: list[SubscriptionDetails] = await subscriptions_controller.return_all_plan_details()
    context = dict(user=user, subscription_account=subscription_account, subscription_plans=subscription_plans)
    return render_template('billing/subscriptions.html', **context)

async def paypal_payment(subscription_details: Subscriptions, user: User):
    """

    :return:
    """
    success_url: str = url_for('subscriptions.subscription_payment_successful', _external=True, _scheme='https')
    failure_url: str = url_for('subscriptions.subscription_payment_failure', _external=True, _scheme='https')
    payment, is_created = await paypal_controller.create_payment(payment_details=subscription_details, user=user,
                                                                 success_url=success_url, failure_url=failure_url)
    if is_created:
        # Redirect user to PayPal for payment approval
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        flash(message=f"Error creating Payment : {payment.error}", category="danger")
        return redirect(url_for('company.get_admin'))


async def make_direct_deposit(subscription_details: Subscriptions, user: User):
    """

    :param subscription_details:
    :param user:
    :return:
    """

    context = dict(user=user, subscription_details=subscription_details)
    return render_template('billing/direct_deposit.html', **context)

@subscriptions_route.post('/subscriptions/payment-method')
@admin_login
async def payment_method_selected(user: User):
    """

    :param user:
    :return:
    """
    payment_method = request.form.get('payment_method')
    subscription_id: str = request.form.get('subscription_id')
    subscription_details: Subscriptions = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

    if subscription_details.subscription_id != subscription_id:
        flash(message="there was a problem making payment for this subscription", category="danger")
        return redirect(url_for('subscriptions.get_subscriptions'))
    if payment_method == "paypal":
        return await paypal_payment(subscription_details=subscription_details, user=user)
    elif payment_method == "payfast":
        return await payfast_controller.payfast_subscription_payment(subscription_details=subscription_details,
                                                                     user=user)
    elif payment_method == "direct_deposit":
        return await make_direct_deposit(subscription_details=subscription_details, user=user)
    print(f"Payment Method: {payment_method}")


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

    subscription = Subscriptions(**subscription_details.dict(), company_id=company_detail.company_id, payments=[])
    await subscriptions_controller.add_update_company_subscription(subscription=subscription)
    flash(message=f"you have successfully created a {subscription.plan_name} Account",category="success")
    return redirect(url_for('subscriptions.get_subscriptions'))


@subscriptions_route.get('/subscriptions/payment/success')
@admin_login
async def subscription_payment_successful(user: User):

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


# MESSAGING TOP UP

@subscriptions_route.post('/_ipn/payfast/package')
async def payfast_package_ipn():
    """
        IF IPN is sent it means either payment succeeded or failed
    :return:
    """
    payfast_dict_data: Dict[str, str] = request.form.to_dict()
    subscription_logger.info(f"Incoming Payment Notification: {payfast_dict_data}")

    # Validate the received data
    if await payfast_controller.is_valid_payfast_data(payfast_dict_data=payfast_dict_data):
        # Extracting relevant fields from the data
        payment_status = payfast_dict_data.get('payment_status')
        amount_gross = payfast_dict_data.get('amount_gross')
        pf_payment_id = payfast_dict_data.get('pf_payment_id')
        item_name = payfast_dict_data.get('item_name')
        email_address = payfast_dict_data.get('email_address')
        merchant_id = payfast_dict_data.get('merchant_id')
        # TODO - send payment receipt and notice welcoming the client to our services
        # Parsing the item_name to get plan_name and payment_type
        plan_name, payment_type = item_name.split("_")

        # Custom fields which might not be present
        subscription_id = payfast_dict_data.get("custom_str1")
        company_id = payfast_dict_data.get("custom_str2")
        uid = payfast_dict_data.get("custom_str3")
        package_id = payfast_dict_data.get("custom_str4")
        subscription_logger.info(f"Verified Request Data For ITN of company: {company_id} ")

        if payment_status == "COMPLETE":
            # Fetch the subscription details based on company_id
            subscription = await subscriptions_controller.get_company_subscription(company_id=company_id)
            subscription_logger.info(f"Able to Retrive the Company Subsciption: {subscription}")
            if isinstance(subscription, Subscriptions):
                # Create a Payment record for the subscription
                try:
                    payment = Payment(
                        subscription_id=subscription.subscription_id,
                        package_id=package_id,
                        amount_paid=amount_gross,
                        payment_method="payfast",
                        is_successful=True,
                        month=1,  # Assuming the payment covers 1 month, adjust if needed
                        comments=f"payfast package payment for company : {company_id}"
                    )
                    subscription_logger.info(f"Created Payment Type : {payment}")

                    # Store the payment in the database
                    payment_data: Payment = await subscriptions_controller.add_company_payment(payment=payment)

                    package_paid = await subscriptions_controller.set_package_to_paid(package_id=package_id)
                    # This Automatically spends the package
                    if package_paid:
                        spent_package = await subscriptions_controller.spend_package(
                            subscription_id=subscription_id, package_id=package_id)
                        if spent_package:
                            subscription_logger.info(f"Package Successfully Spent")

                    subscription_logger.info(f"Payment Record Created: {payment_data}")
                    # Return a success response
                    return jsonify(
                        dict(message=f"Successfully paid for {plan_name} subscription", data=payfast_dict_data)), 200
                except ValidationError as e:
                    subscription_logger.warning(str(e))

            else:
                subscription_logger.warning(f"Could not Verify if subscription is of the type Subscrtiption")

            subscription_logger.warning(f"Payment not complete or not a subscription: {payfast_dict_data}")
            return jsonify(dict(message="Payment not complete or invalid payment type", data=payfast_dict_data)), 400

        else:
            # Log the issue or handle failed payment status
            subscription_logger.warning(f"Payment not complete or not a subscription: {payfast_dict_data}")
            return jsonify(dict(message="Payment not complete or invalid payment type", data=payfast_dict_data)), 400
    else:
        # Handle invalid data, possibly log and alert
        subscription_logger.warning(f"Invalid PayFast data received: {payfast_dict_data}")
        return jsonify(dict(message="Invalid data received", data=payfast_dict_data)), 400


@subscriptions_route.post('/subscriptions/topup')
@admin_login
async def messaging_top_up(user: User):
    """
    :param user:
    :return:
    """
    if not user.company_id:
        message: str = "You are not a member of any company therefore you cannot buy any topup packs"
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
        message: str = """You have no Valid subscription - please Subscribe and pay for your Subscription before 
        buying any Top Up Packs"""
        flash(message=message, category="danger")
        subscription_logger.info(message)
        return redirect(url_for('company.get_admin'))


    package: Package = await subscriptions_controller.add_update_sms_email_package(top_up_pack=top_up_pack)
    if package:
        payfast_payment_endpoint = await payfast_controller.payfast_package_create_payment(
            subscription_details=subscription,top_up_pack=package, user=user)
        if payfast_payment_endpoint:
            return payfast_payment_endpoint


    message: str = """Please try buying Top Up Packs Later - there was an error on our side"""
    flash(message=message, category="danger")
    subscription_logger.info(message)
    return redirect(url_for('company.get_admin'))

@subscriptions_route.get('/subscriptions/package/success/<string:package_id>')
@admin_login
async def package_payment_successful(user: User, package_id: str):
    """
        This is for PayPal Payments
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
