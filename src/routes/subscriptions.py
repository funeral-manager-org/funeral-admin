import json

from flask import Blueprint, url_for, flash, redirect, request

from src.database.models.payments import Payment
from src.authentication import login_required
from src.database.models.subscriptions import PlanNames, SubscriptionDetails, Subscriptions
from src.database.models.users import User
from src.main import company_controller, paypal_controller, subscriptions_controller

subscriptions_route = Blueprint('subscriptions', __name__)


@subscriptions_route.post('/subscriptions/subscribe/<string:option>')
@login_required
async def do_subscribe(user: User, option: str):
    """

    :param option:
    :param user:
    :return:
    """
    if not user.company_id:
        flash(message="You cannot subscribe please ensure to create a company", category="danger")
        return redirect(url_for('home.get_home'))

    if option not in PlanNames.plan_names():
        flash(message="Please select a valid subscription plan", category="danger")
        return redirect('company.get_admin')

    company_detail = await company_controller.get_company_details(company_id=user.company_id)

    subscription_details: SubscriptionDetails = SubscriptionDetails().create_plan(plan_name=option)

    success_url: str = url_for('subscriptions.get_success_url')
    failure_url: str = url_for('subscriptions.get_failure_url')

    payment, is_created = await paypal_controller.create_payment(subscription_details=subscription_details,
                                                                 success_url=success_url,
                                                                 failure_url=failure_url)

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
@login_required
async def payment_successful(user: User):
    pass

    try:
        # Load JSON data
        _payload = request.json
        _signature = request.headers.get('Paypal-Transmission-Sig')
        request_valid = await paypal_controller.verify_signature(payload=_payload, signature=_signature)
        if not request_valid:
            redirect(url_for('home.get_home'))

        data = request.json

        # Extract payment amount
        amount = int(_payload.get("resource", {}).get("amount", {}).get("total"))
        subscription = await subscriptions_controller.get_company_subscription(company_id=user.company_id)

        payment = Payment(subscription_id=subscription.subscription_id,
                          amount_paid=amount,
                          payment_method="paypal",
                          is_successful=True, month=1)

        payment = await subscriptions_controller.add_company_payment(payment=payment)

        if amount < subscription.subscription_amount:
            flash(message=f"you have paid : {amount} instead of {subscription.subscription_amount}", category="danger")

        else:
            flash(message=f"Payment Of {amount} Made Successfully", category="success")

        return redirect(url_for('company.get_admin'))

        # Convert amount to float
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


@subscriptions_route.get('/subscriptions/payment/failure')
@login_required
async def payment_failure():
    pass
