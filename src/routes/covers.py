from datetime import datetime

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.sql.covers import PolicyRegistrationDataORM
from src.logger import init_logger
from src.database.models.covers import ClientPersonalInformation, PolicyRegistrationData, Premiums, PaymentFrequency, \
    PaymentStatus, PremiumReceipt
from src.authentication import login_required, user_details
from src.database.models.companies import CoverPlanDetails, CompanyBranches, Company
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
        return redirect(url_for('home.get_home'))

    plan_cover = await company_controller.get_plan_cover(company_id=company_id, plan_number=plan_number)
    policy_subscribers = await company_controller.get_plan_subscribers(plan_number=plan_number)

    sorted_by_paid = sorted(policy_subscribers, key=lambda policy: bool(
        policy.get_this_month_premium()) and policy.get_this_month_premium().is_paid)
    sorted_by_paid.reverse()
    subscribed_clients = dict(
        policies=sorted_by_paid,
        total_policies=len(policy_subscribers),
        total_premiums=sum([policy.total_premiums for policy in policy_subscribers or []
                            if isinstance(policy, PolicyRegistrationData)]),

        total_premiums_paid=len([1 for policy in policy_subscribers or []
                                 if isinstance(policy.get_this_month_premium(),
                                               Premiums) and policy.get_this_month_premium().is_paid]),
        # only adds if we have a premium this month and the premium is paid
        total_amount_paid=sum([policy.get_this_month_premium().amount_paid for policy in policy_subscribers or []
                               if isinstance(policy.get_this_month_premium(),
                                             Premiums) and policy.get_this_month_premium().is_paid]),
        summary_month=PolicyRegistrationData.report_month_in_words()
    )
    context = dict(user=user, plan_cover=plan_cover, subscribers_data=subscribed_clients)
    return render_template('admin/managers/covers/view.html', **context)


async def get_client_list(user: User) -> tuple[str, list[CompanyBranches], list[ClientPersonalInformation]]:
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    if not company_branches:
        flash(message="please define your company branches", category="danger")
        return None, None, None

    # if this is not a post message then the request is being sent by menu links
    branch_id = request.form.get('branch_id', None)
    if not branch_id and company_branches:
        branch_id = company_branches[-1].branch_id

    clients_list: list[ClientPersonalInformation] = await company_controller.get_branch_policy_holders(
        branch_id=branch_id)
    return branch_id, company_branches, clients_list


@covers_route.route('/admin/premiums/current/<int:page>/<int:count>', methods=['GET', 'POST'])
@login_required
async def get_current_premiums_paged(user: User, page: int = 0, count: int = 25):
    """

    :param count:
    :param page:
    :param user:
    :return:
    """
    if (page > 1000) or (count > 1000):
        flash(message="your request is out of bounds", category="danger")
        return redirect(url_for('home.get_home'))

    branch_id, company_branches, clients_list = await get_client_list(user=user)
    if not branch_id:
        flash(message="Error retrieving premiums please try again later", category="danger")
        return redirect(url_for('admin.get_admin'))

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
                   company_branches=company_branches,
                   payment_status=PaymentStatus,
                   policy_data_list=policy_data_list,
                   page=page, count=count)

    return render_template('admin/premiums/current.html', **context)


@covers_route.route('/admin/premiums/outstanding/<int:page>/<int:count>', methods=['POST', 'GET'])
@login_required
async def get_outstanding_premiums(user: User, page: int = 0, count: int = 25):
    """

    :param count:
    :param page:
    :param user:
    :return:
    """
    if (page > 1000) or (count > 1000):
        flash(message="your request is out of bounds", category="danger")
        return redirect(url_for('home.get_home'))

    branch_id, company_branches, clients_list = await get_client_list(user=user)
    if not branch_id:
        flash(message="Error retrieving premiums please try again later", category="danger")
        return redirect(url_for('admin.get_admin'))

    policy_data_list: list[PolicyRegistrationData] = await covers_controller.get_outstanding_branch_policy_data_list(
        branch_id=branch_id, page=page, count=count)

    context = dict(user=user, clients_list=clients_list, branch_id=branch_id,
                   company_branches=company_branches,
                   payment_status=PaymentStatus,
                   policy_data_list=policy_data_list,
                   page=page, count=count)

    return render_template('admin/premiums/outstanding.html', **context)


@covers_route.get('/admin/premiums/quick-pay')
@login_required
async def get_quick_pay(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    if company_branches:
        flash(message="Please Select Branch to Update or View Payment Records", category="success")
    else:
        flash(message="Snapped! - This is either a Terrible Error or you do not have any branches in your company",
              category="danger")

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
    clients_list: list[ClientPersonalInformation] = []

    # Extract form data
    branch_id: str = request.form.get('branch_id', None)
    client_id: str = request.form.get('client_id', None)
    payment_method: str = request.form.get('payment_method', None)

    actual_amount_str = request.form.get('actual_amount', '0')
    actual_amount: int = int(actual_amount_str) if actual_amount_str.isdigit() else 0

    # Fetch company branches
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)

    context = {
        'user': user,
        'company_branches': company_branches,
        'payment_status': PaymentStatus
    }

    valid_pm_methods: list[str] = await company_controller.get_payment_methods()

    # Check if payment_method is not in the valid payment methods
    if payment_method is not None and payment_method not in valid_pm_methods:
        flash(message="Invalid payment method selected", category="danger")
        return redirect(url_for('covers.get_quick_pay'))

    if branch_id:
        # Loading Branch Clients
        try:
            branch_details: CompanyBranches | dict = next(
                (branch for branch in company_branches if branch.branch_id == branch_id),
                {})

            if not branch_details:
                return redirect(url_for('covers.get_quick_pay'))

            if user.company_id != branch_details.company_id:
                flash(message="Something is Terribly wrong or you are not authorized to view this resource",
                      category="danger")
                return redirect(url_for('home.get_home'))

        except StopIteration as e:
            covers_logger.error("Unable to find branch details - this should not happen")
            flash(message="This is a Terrible Error - We Obviously Did Something wrong please report this",
                  category="danger")
            branch_details = {}

        if branch_details:
            # Note there are possibilities where a policyholder still will not have an actual policy -
            clients_list = await company_controller.get_branch_policy_holders(branch_id=branch_id)

            # removing clients without actual policy numbers
            # this will allow the employee to select from only clients who are policyholders
            clients_list = [client for client in clients_list if client.policy_number]

            context.update(branch_details=branch_details)
            context.update(clients_list=clients_list)

    # Fetch selected client and policy data if client_id is provided
    if client_id and clients_list:
        try:
            selected_client = next((client for client in clients_list if client.uid == client_id), None)
        except StopIteration as e:
            selected_client = None

        if selected_client:
            policy_data = await covers_controller.get_policy_data(policy_number=selected_client.policy_number)
            if policy_data:
                # Ensure this month's premium is forecasted
                if not policy_data.get_this_month_premium():
                    await covers_controller.create_forecasted_premiums(policy_number=policy_data.policy_number)
                    policy_data = await covers_controller.get_policy_data(policy_number=selected_client.policy_number)

                covers_logger.info(f"Total balance Due : {str(policy_data.total_balance_due)}")

                payment_methods = await company_controller.get_payment_methods()
                context.update(selected_client=selected_client, policy_data=policy_data,
                               payment_methods=payment_methods)
            else:
                flash("There is no Policy Associated with the selected Client, We cannot Process Payment",
                      category="danger")
        else:
            # selected client not found either we changed the branch or there is a big error
            pass
    else:
        # This is so that employees can be informed of the next action to take
        if branch_id and not clients_list:
            flash(message="Branch Do not have active clients", category="danger")
        else:
            flash(message="Select Client to Make / Check Payment", category="success")

    if policy_data:
        premium: Premiums = policy_data.get_this_month_premium()
        context.update(premium=premium, policy_data=policy_data)
    # Process the premium payment if all required data is available
    if selected_client and policy_data and actual_amount > 0 and payment_method:
        # should rather allow the employee to choose the premium to make payment for

        if premium and not premium.is_paid:
            premium.amount_paid = actual_amount
            premium.date_paid = datetime.now().date()
            premium.payment_method = payment_method
            premium.payment_status = PaymentStatus.PAID.value
            premium.next_payment_amount = premium.payment_amount

            paid_premium: Premiums = await covers_controller.add_update_premiums_payment(premium_payment=premium)
            context.update(paid_premium=paid_premium)

            # creating a log of this payment
            log_mess: str = f'Paid Premium: {paid_premium.premium_id} {paid_premium.amount_paid}'
            covers_logger.info(log_mess)

            is_sent = await covers_controller.send_premium_payment_notification(premium=paid_premium,
                                                                                policy_data=policy_data)
            if not is_sent:
                # Could Not Send payment Notifications either by email or SMS
                covers_logger.info("failed to send payment notifications please complete the client contact records")
                flash(message="failed to send payment notifications please complete the client contact records",
                      category='danger')

            # TODO Create payment Receipt - right now
            company_details: Company = await company_controller.get_company_details(company_id=user.company_id)
            if company_details:
                receipt = await covers_controller.create_invoice_record(premium=paid_premium)
                context.update(company=company_details,  receipt=receipt, premium=paid_premium, generated_on=datetime.now())
                # TODO - create a better invoice title
                title = f"{company_details.company_name} Invoice - Premium Payment"
                context.update(title=title)

            return render_template('admin/premiums/receipt.html', **context)


        message: str = "Premium is already paid" if premium else ("There are not active premiums associated with "
                                                                  "this policy holder")

        flash(message=message, category="danger")

    return render_template('admin/premiums/pay.html', **context)


@covers_route.get('/admin/premiums/receipt/<string:receipt_number>')
@user_details
async def receipt_reprint_receipt_number(user: User, receipt_number: str):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    receipt = await covers_controller.get_receipt_by_receipt_number(receipt_number=receipt_number)
    if not isinstance(receipt, PremiumReceipt):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))


    policy_number = receipt.premium.policy_number
    policy_data: PolicyRegistrationDataORM = await covers_controller.get_policy_data(policy_number=policy_number)
    if not isinstance(policy_data, PolicyRegistrationData):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))

    selected_client = await company_controller.get_policy_holder_by_policy_number(policy_number=policy_number)

    company_details = await company_controller.get_company_details(company_id=policy_data.company_id)

    if not isinstance(company_details, Company):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))


    context.update(company=company_details, policy_data=policy_data, selected_client=selected_client,  receipt=receipt,
                   premium=receipt.premium, generated_on=datetime.now())

    return render_template('admin/premiums/receipt.html', **context)


@covers_route.get('/admin/premiums/last-receipt/<string:premium_id>')
@user_details
async def last_receipt_reprint(user: User, premium_id: str):
    """

    :param user:
    :return:
    """

    context = dict(user=user)
    receipt = await covers_controller.get_last_receipt_by_premium_number(premium_id=premium_id)

    covers_logger.info(f'Receipt Ticket: {receipt}')

    if not isinstance(receipt, PremiumReceipt):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))


    policy_number = receipt.premium.policy_number
    policy_data: PolicyRegistrationDataORM = await covers_controller.get_policy_data(policy_number=policy_number)
    covers_logger.info(f"Policy Data: {policy_data}")
    if not isinstance(policy_data, PolicyRegistrationData):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))

    selected_client = await company_controller.get_policy_holder_by_policy_number(policy_number=policy_number)

    company_details = await company_controller.get_company_details(company_id=policy_data.company_id)
    covers_logger.info(f"Company Details : {company_details}")
    if not isinstance(company_details, Company):
        flash(message="Receipt not found", category="danger")
        return redirect(url_for('covers.get_quick_pay'))


    context.update(company=company_details,policy_data=policy_data, selected_client=selected_client, receipt=receipt,
                   premium=receipt.premium, generated_on=datetime.now())

    return render_template('admin/premiums/receipt.html', **context)
