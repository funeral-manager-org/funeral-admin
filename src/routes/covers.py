from datetime import datetime

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.logger import init_logger
from src.database.models.covers import ClientPersonalInformation, PolicyRegistrationData, Premiums, PaymentFrequency, \
    PaymentStatus
from src.authentication import login_required
from src.database.models.companies import CoverPlanDetails, CompanyBranches
from src.database.models.users import User
from src.main import company_controller, covers_controller

covers_route = Blueprint('covers', __name__)
covers_logger = init_logger('covers_logger')


@covers_route.get('/admin/administrator/plans')
@login_required
async def get_covers(user: User):
    """

        :param user:
        :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    cover_details = await company_controller.get_company_covers(company_id=user.company_id)
    context = dict(user=user, branches=company_branches, cover_details=cover_details)
    return render_template('admin/managers/covers.html', **context)


@covers_route.post('/admin/administrator/plans/add-plan-cover')
@login_required
async def add_plan_cover(user: User):
    """
        :param user:
        :return:
    """
    try:
        plan_cover = CoverPlanDetails(**request.form)
        plan_cover.company_id = user.company_id
    except ValidationError as e:
        covers_logger.error(str(e))
        flash(message="Unable to create plan please provide all necessary details", category="danger")
        return redirect(url_for('covers.get_covers'))

    updated_plan_cover = await company_controller.create_plan_cover(plan_cover=plan_cover)

    flash(message="successfully created plan", category="success")
    return redirect(url_for('covers.get_covers'))


@covers_route.get('/admin/administrator/plan/<string:company_id>/<string:plan_number>')
@login_required
async def get_plan_cover(user: User, company_id: str, plan_number: str):
    """

    :param user:
    :param company_id:
    :param plan_number:
    :return:
    """
    if user.company_id != company_id:
        flash(message="You are not authorized to view the cover details", category="danger")
        return redirect('home.get_home')

    plan_cover = await company_controller.get_plan_cover(company_id=company_id, plan_number=plan_number)
    subscribed_clients = await company_controller.get_plan_subscribers(plan_number=plan_number)
    context = dict(user=user, plan_cover=plan_cover, subscribed_clients=subscribed_clients)
    return render_template('admin/managers/covers/view.html', **context)


@covers_route.route('/admin/premiums/current/<int:page>/<int:count>', methods=['GET', 'POST'])
@login_required
async def get_current_premiums_paged(user: User, page: int = 0, count: int = 25):
    """

    :param count:
    :param page:
    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)

    # if this is not a post message then the request is being sent by menu links
    branch_id = request.form.get('branch_id', None)
    if not branch_id:
        branch_id = company_branches[-1].branch_id

    clients_list: list[ClientPersonalInformation] = await company_controller.get_branch_policy_holders(
        branch_id=branch_id)

    policy_data_list: list[PolicyRegistrationData] = await covers_controller.get_branch_policy_data_list(
        branch_id=branch_id, page=page, count=count)
    client_policy_data = {}

    # TODO use this structure instead to display results
    for client in clients_list:
        for policy in policy_data_list:
            if client.policy_number == policy.policy_number:
                client_policy_data[client.uid] = {
                    "policy_number": client.policy_number,
                    "client": client.dict(),
                    "policy_data": policy.dict()
                }

    context = dict(user=user, clients_list=clients_list, branch_id=branch_id,
                   company_branches=company_branches, policy_data_list=policy_data_list,
                   page=page, count=count)

    return render_template('admin/premiums/current.html', **context)


@covers_route.get('/admin/premiums/outstanding')
@login_required
async def get_outstanding_premiums(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('admin/premiums/outstanding.html', **context)


@covers_route.get('/admin/premiums/quick-pay')
@login_required
async def get_quick_pay(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)

    context = dict(user=user, company_branches=company_branches)
    return render_template('admin/premiums/pay.html', **context)


@covers_route.post('/admin/premiums/current/branch')
@login_required
async def premiums_payments(user: User):
    """
    Retrieve the current premiums for a branch and optionally a selected client.
    """
    # Initialize variables
    policy_data: PolicyRegistrationData | None = None
    selected_client: ClientPersonalInformation | None = None

    # Extract form data
    branch_id: str = request.form.get('branch_id', None)
    client_id: str = request.form.get('client_id', None)
    payment_method: str = request.form.get('payment_method', None)
    actual_amount: int = int(request.form.get('actual_amount', 0))

    # Fetch company branches
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = {
        'user': user,
        'company_branches': company_branches,
        'payment_status': PaymentStatus
    }

    # Fetch branch details and clients list if branch_id is provided
    clients_list: list[ClientPersonalInformation] = []

    if branch_id:
        branch_details = next((branch for branch in company_branches if branch.branch_id == branch_id), None)
        if branch_details:
            context.update(branch_details=branch_details)

        clients_list = await company_controller.get_branch_policy_holders(branch_id=branch_id)
        context.update(clients_list=clients_list)

    # Fetch selected client and policy data if client_id is provided
    if client_id and clients_list:
        selected_client = next((client for client in clients_list if client.uid == client_id), None)
        if selected_client:
            policy_data = await covers_controller.get_policy_data(policy_number=selected_client.policy_number)
            if policy_data:
                # Ensure this month's premium is forecasted
                if not policy_data.get_this_month_premium():
                    await covers_controller.create_forecasted_premiums(policy_number=policy_data.policy_number)
                    policy_data = await covers_controller.get_policy_data(policy_number=selected_client.policy_number)

                covers_logger.info(f"Total balance Due : {str(policy_data.total_balance_due)}")

                payment_methods = await company_controller.get_payment_methods()
                context.update(selected_client=selected_client, policy_data=policy_data, payment_methods=payment_methods)
            else:
                flash("There is no cover associated with this Policy Holder, We cannot Process Payment", category="danger")

    # Process the premium payment if all required data is available
    if selected_client and policy_data and actual_amount and payment_method:
        premium = policy_data.get_first_unpaid()
        if not premium:
            premium.amount_paid = actual_amount
            premium.date_paid = datetime.now().date()
            premium.payment_method = payment_method
            premium.payment_status = PaymentStatus.PAID.value
            premium.next_payment_amount = premium.payment_amount

            paid_premium = await covers_controller.add_update_premiums_payment(premium_payment=premium)
            covers_logger.info(f'Covers Paid Premium Logger: {paid_premium.premium_id} {paid_premium.amount_paid} {paid_premium.is_paid}')

            context.update(paid_premium=paid_premium)
            return render_template('admin/premiums/receipt.html', **context)

        flash("Premium Already Paid", category="success")

    return render_template('admin/premiums/pay.html', **context)
