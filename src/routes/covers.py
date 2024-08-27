from datetime import datetime

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.models.bank_accounts import BankAccount, AccountTypes
from src.authentication import login_required, user_details
from src.database.models.companies import CoverPlanDetails, CompanyBranches, Company, EmployeeDetails
from src.database.models.covers import ClientPersonalInformation, PolicyRegistrationData, Premiums, PaymentStatus, \
    PremiumReceipt, BeginClaim, Claims, RelationshipToPolicyHolder, ClaimantPersonalDetails
from src.database.models.users import User
from src.database.sql.covers import PolicyRegistrationDataORM
from src.logger import init_logger
from src.main import company_controller, covers_controller, subscriptions_controller
from src.utils import is_valid_ulid, claims_upload_folder, load_claims_files_in_folder, save_files_to_folder

covers_route = Blueprint('covers', __name__)
covers_logger = init_logger('covers_logger')


def validate_page_and_count(page: int, count: int, max_value: int = 1000, redirect_route: str = 'home.get_home'):
    """
    Validates the page and count values and handles out-of-bounds errors.

    :param page: The page number to check.
    :param count: The count number to check.
    :param max_value: The maximum allowed value for page and count.
    :param redirect_route: The route to redirect to in case of error.
    :return: A boolean indicating whether the validation passed.
    """
    if page > max_value or count > max_value:
        flash(message="Your request is out of bounds", category="danger")
        return redirect(url_for(redirect_route))
    return None


@covers_route.get('/admin/administrator/plans')
@login_required
async def get_covers(user: User):
    """
    :param user:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    # Retrieve company branches and cover details
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    cover_details = await company_controller.get_company_covers(company_id=user.company_id)

    # Validate that the returned data is not empty or None
    if not company_branches:
        covers_logger.warning(f"Company branches not found for company ID {user.company_id}")
        flash('Company branches not found.', 'danger')
        return redirect(url_for('company.get_admin'))

    if not cover_details:
        covers_logger.warning(f"Cover details not found for company ID {user.company_id}")
        flash('Cover details not found. please create new covers for your company', 'success')

    # Create context and render template if data is valid
    context = dict(user=user, branches=company_branches, cover_details=cover_details)
    return render_template('admin/managers/covers.html', **context)


@covers_route.post('/admin/administrator/plans/add-plan-cover')
@login_required
async def add_plan_cover(user: User):
    """
    :param user:
    :return:
    """
    # Attempt to create a plan cover using form data
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    try:
        plan_cover = CoverPlanDetails(**request.form)
    except ValidationError as e:
        covers_logger.error(str(e))
        flash(message="Unable to create plan please provide all necessary details", category="danger")
        return redirect(url_for('covers.get_covers'))

    if not user.company_id:
        flash(message="User Not Registered in a company", category="danger")
        return redirect(url_for('covers.get_covers'))

    plan_cover.company_id = user.company_id

    # Create the plan cover and flash success
    updated_plan_cover = await company_controller.create_plan_cover(plan_cover=plan_cover)

    if not updated_plan_cover:
        flash(message="Bad Error updating or creating a new cover please try again later", category="danger")
        return redirect(url_for('covers.get_covers'))

    flash(message="Successfully created plan.", category="success")
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
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    if not is_valid_ulid(value=plan_number):
        flash(message="Could not verify your request (Request Contains bad data)", category="danger")
        return redirect(url_for('company.get_admin'))

    if not is_valid_ulid(value=company_id):
        flash(message="Could not verify your request (Request Contains bad data)", category="danger")
        return redirect(url_for('company.get_admin'))

    if (user.company_id is None) or (user.company_id != company_id):
        flash(message="You are not authorized to view the cover details", category="danger")
        return redirect(url_for('home.get_home'))

    plan_cover = await company_controller.get_plan_cover(company_id=company_id, plan_number=plan_number)
    if not plan_cover:
        flash(message="Unable to retrieve cover details, please try again later", category="danger")
        return redirect(url_for('company.get_admin'))

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


async def get_client_list(user: User) -> tuple[
    str | None, list[CompanyBranches] | None, list[ClientPersonalInformation] | None]:
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

    clients_list = await company_controller.get_branch_policy_holders(branch_id=branch_id)
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
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    redirect_on_bad_page_count = validate_page_and_count(page=page, count=count)
    if redirect_on_bad_page_count:
        return redirect_on_bad_page_count

    if (page > 1000) or (count > 1000):
        flash(message="your request is out of bounds", category="danger")
        return redirect(url_for('home.get_home'))

    branch_id, company_branches, clients_list = await get_client_list(user=user)
    if (not branch_id) or (not company_branches):
        flash(message="Error retrieving premiums please try again later", category="danger")
        return redirect(url_for('admin.get_admin'))

    policy_data_list: list[PolicyRegistrationData] = await covers_controller.get_branch_policy_data_list(
        branch_id=branch_id, page=page, count=count)

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
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    redirect_on_bad_page_count = validate_page_and_count(page=page, count=count)
    if redirect_on_bad_page_count:
        return redirect_on_bad_page_count

    branch_id, company_branches, clients_list = await get_client_list(user=user)
    if (not branch_id) or (not company_branches):
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
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

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
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

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
            covers_logger.error(str(e))
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
        premium: Premiums | None = policy_data.get_this_month_premium()
        context.update(premium=premium, policy_data=policy_data)
    else:
        premium = None
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
                context.update(company=company_details, receipt=receipt, premium=paid_premium,
                               generated_on=datetime.now())
                # TODO - create a better invoice title
                title = f"{company_details.company_name} Invoice - Premium Payment"
                context.update(title=title)

            return render_template('receipts/companies/premium_payment_receipt.html', **context)

        message: str = "Premium is already paid" if premium else ("There are not active premiums associated with "
                                                                  "this policy holder")

        flash(message=message, category="danger")

    return render_template('admin/premiums/pay.html', **context)


# noinspection DuplicatedCode
@covers_route.get('/admin/premiums/receipt/<string:receipt_number>')
@user_details
async def receipt_reprint_receipt_number(user: User, receipt_number: str):
    """

    :param user:
    :return:
    """
    if not is_valid_ulid(value=receipt_number):
        flash(message="Could not verify your request (Request Contains bad data)", category="danger")
        return redirect(url_for('company.get_admin'))

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

    context.update(company=company_details, policy_data=policy_data, selected_client=selected_client, receipt=receipt,
                   premium=receipt.premium, generated_on=datetime.now())

    return render_template('receipts/companies/premium_payment_receipt.html', **context)


@covers_route.get('/admin/premiums/last-receipt/<string:premium_id>')
@user_details
async def last_receipt_reprint(user: User, premium_id: str):
    """

    :param user:
    :return:
    """
    if not is_valid_ulid(value=premium_id):
        flash(message="Could not verify your request (Request Contains bad data)", category="danger")
        return redirect(url_for('company.get_admin'))

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

    context.update(company=company_details, policy_data=policy_data, selected_client=selected_client, receipt=receipt,
                   premium=receipt.premium, generated_on=datetime.now())

    return render_template('receipts/companies/premium_payment_receipt.html', **context)


@covers_route.get('/covers/get-claim-form')
@login_required
async def get_claim_form(user: User):
    """
        **get_claim_form**
    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template("claims/claim_form.html", **context)


@covers_route.post('/covers/claims/retrive-policy')
@login_required
async def retrieve_policy(user: User):
    """
        **retrieve_policy**
    :param user:
    :return:
    """

    # TODO create a wrapper as a route Guard can be created in subscription controller
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    try:
        claim_init_data = BeginClaim(**request.form)
    except ValidationError as e:
        covers_logger.warning(str(e))
        flash(message="Please ensure your policy number and id number are correct", category="danger")
        return redirect(url_for('covers.get_claim_form'))

    policy_data: PolicyRegistrationData = await covers_controller.get_policy_data(
        policy_number=claim_init_data.policy_number)
    # Ensuring there is a Policy Attached to the Policy Number
    if not isinstance(policy_data, PolicyRegistrationData):
        mess: str = f"""The Policy with Policy Number : {str(claim_init_data.policy_number)} was not found please be 
        sure to enter your information correctly"""
        flash(message=mess, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    # Ensuring the User Should be processing the Claim
    if user.company_id != policy_data.company_id:
        message: str = f"""You are not Authorized to process this claim please inform your administrator"""
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    # if Policy Owes Some Amount it will inform the employee and Continue
    if policy_data.total_balance_due > 0:
        mess: str = f"There is an Outstanding Premium to the amount of R {policy_data.total_balance_due} on this Policy"
        flash(message=mess, category="success")

    client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
        id_number=claim_init_data.id_number)

    # Checking if PolicyHolder is Found
    # TODO Need to Revise this to allow every covered Member to Claim on this Policy
    # if not (client_data and client_data.is_policy_holder):
    #     message: str = f"""The Supplied ID Number is not of the Policy Holder- please submit the
    #     Policy Holder ID Number"""
    #     flash(message=message, category="danger")
    #     return redirect(url_for('covers.get_claim_form'))

    # Ensuring The Client has the Same Policy Number as the Supplied Policy Number
    if client_data.policy_number != claim_init_data.policy_number:
        message: str = f"""We are unable to ascertain any relationship between the id number and policy number"""
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    # TODO: Initiate the Claim
    # - Present the policy information and claim form to the claimant or responsible employee.
    # - Ensure that the signed policy document is attached to the claim.
    # - Collect and attach claimant information, including contact details and relationship to the deceased.
    # - Attach all relevant documentation related to the deceased (e.g., death certificate, identification, legal documents).
    # TODO: Submit the Claim
    # - Verify that all required documents and information are attached.
    # - Submit the fully completed claim form for processing.
    # TODO: Claim Review and Decision
    # - Review the claim by the responsible person or department within the company.
    # - Make a decision regarding the claim’s approval or rejection.

    # TODO: Notification and Communication
    # - Notify the employee responsible for creating the claim about the decision.
    # - Inform the claimant and all other relevant parties about the decision.
    # - Provide detailed information about the next steps, if any.

    # TODO: Work Order Creation (if applicable)
    # - If the claim involves services such as financial compensation, burial arrangements, or memorial services:
    #   - Create a work order.
    #   - Assign the work order to relevant departments (e.g., Finance, Tombstones and Graveyard, Family Services).

    # TODO: Follow-Up and Support
    # - Ensure that all involved departments carry out their responsibilities in a timely manner.
    # - Provide ongoing communication and support to the claimant and family, ensuring they are informed of the claim’s progress.

    # TODO: Completion and Documentation
    # - Once all tasks related to the claim are completed:
    #   - Document the outcomes.
    #   - Close the claim, ensuring all records are securely stored and accessible for future reference.

    context = dict(policy_holder=client_data, policy_data=policy_data)
    return render_template("claims/sections/policy.html", **context)


async def create_claim_return_context(user: User, policy_number: str, id_number: str):
    """
        Will create an Actual Claim and Returns the Context for the Employee to Continue with the Claim Process
    :param user:
    :param policy_number:
    :param id_number:
    :return:
    """

    policy_data: PolicyRegistrationData = await covers_controller.get_policy_data(policy_number=policy_number)


    if not isinstance(policy_data, PolicyRegistrationData):
        message: str = "Policy Does not Exist"
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
        id_number=id_number)

    if not isinstance(client_data, ClientPersonalInformation):
        message: str = "Client Data Does Not Exist"
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    employee_details: EmployeeDetails = await company_controller.get_employee_by_uid(uid=user.uid)
    if not (isinstance(employee_details, EmployeeDetails) and employee_details.company_id == policy_data.company_id):
        message: str = "Employee not Authorized to process this claim"
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    plan_details: CoverPlanDetails = await company_controller.get_plan_cover(company_id=policy_data.company_id,
                                                                             plan_number=policy_data.plan_number)
    if not isinstance(plan_details, CoverPlanDetails):
        message: str = "Fatal Error processing Claim please inform admin"
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    # Checking if claim for this individual has already been logged
    claim_data: Claims = await covers_controller.get_claim_with_policy_number_and_id_number(
        policy_number=policy_number, id_number=id_number)

    if not isinstance(claim_data, Claims):
        new_claim: Claims = Claims(employee_id=employee_details.employee_id,
                                   branch_id=policy_data.branch_id,
                                   company_id=policy_data.company_id,
                                   plan_number=policy_data.plan_number,
                                   policy_number=policy_data.policy_number,
                                   member_id_number=id_number,
                                   claim_amount=plan_details.coverage_amount,
                                   claimed_for_uid=client_data.uid,
                                   claim_type=plan_details.plan_type)
        covers_logger.info(f"Creating New Claim: {new_claim}")
        claim_data: Claims = await covers_controller.add_claim(claim_data=new_claim)

    if not isinstance(claim_data, Claims):
        message: str = "Unable to create claim please try again later"
        flash(message=message, category="danger")
        return redirect(url_for('covers.get_claim_form'))

    context = dict(user=user, policy_data=policy_data, client_data=client_data, employee_details=employee_details,
                   plan_details=plan_details, claim_data=claim_data)
    return context


async def redirect_log_claim_with_query(claim_number: str, id_number: str, policy_number: str):
    _url = url_for('covers.log_claim', policy_number=policy_number, id_number=id_number)
    _redirect_link = f"{_url}?claim_number={claim_number}"
    return redirect(_redirect_link)


@covers_route.route('/covers/claims/log-claim/<string:policy_number>/<string:id_number>', methods=['POST', 'GET'])
@login_required
async def log_claim(user: User, policy_number: str, id_number: str):
    """
    :param user:
    :param policy_number:
    :param id_number:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
        id_number=id_number)

    if request.method.casefold() == "get":
        # Check if claim_number is present as a query parameter
        old_claim = await covers_controller.get_claim_with_policy_number_and_id_number(policy_number=policy_number,
                                                                                       id_number=id_number)
        claim_number = request.args.get('claim_number')

        if not isinstance(old_claim, Claims):
            if claim_number:
                covers_logger.info(f"Claim number {claim_number} found in query parameters.")
                # Use the claim_number to retrieve additional data or attach it to the context
                claim_data = await covers_controller.get_claim_data(claim_number=claim_number)
                context = dict(claim_data=claim_data, user=user, client_data=client_data)
            else:
                context = await create_claim_return_context(user=user, policy_number=policy_number, id_number=id_number)
                if not isinstance(context, dict):
                    # If it is not context then it's a redirect, return it
                    return context

        else:
            # Need to set the claim number to the old claims claim number
            claim_number = old_claim.claim_number
            context = dict(claim_data=old_claim, user=user, client_data=client_data)

        # retrieve Old Information if existing
        context.update(policy_number=policy_number, id_number=id_number)

        # if a claim was previously being logged then it will be retrieved and presented to the form so the user
        # can change it
        old_claimant_data = await covers_controller.get_claimant_data(claim_number=claim_number)
        # Add Existing Data into the form so the user can edit this data because the claim already exists
        covers_logger.info(f"OLD Claimant Data: {old_claimant_data}")
        if isinstance(old_claimant_data, ClaimantPersonalDetails):
            context.update(old_claimant_data=old_claimant_data)

        relation_ships = RelationshipToPolicyHolder.relationships()
        if relation_ships:
            context.update(relation_ships=relation_ships)

        return render_template('claims/sections/claimant_data.html', **context)

    # Request is POST - we need to capture Claimant personal information
    try:
        claimant_details = ClaimantPersonalDetails(**request.form)
        covers_logger.info(f"CLAIMANT DATA : {claimant_details}")
    except ValidationError as e:
        covers_logger.warning(str(e))
        # claim number is always present on claimant data form
        claim_number = request.form.get('claim_number') or request.args.get('claim_number')
        # claim_data = await covers_controller.get_claim_data(claim_number=claim_number)
        flash(message="Please provide all the information for the claimant - Correctly", category="danger")
        return await redirect_log_claim_with_query(claim_number, id_number, policy_number)

    # if we are here it means claimant data is provided correctly
    # this will create new claimant record or update existing one
    claimant_data: ClaimantPersonalDetails = await covers_controller.add_claimant_data(
        claimant_details=claimant_details)

    if not isinstance(claimant_data, ClaimantPersonalDetails):
        message: str = "Unable to Add Claimant Data - please try again"
        flash(message=message, category="danger")
        claim_number = claimant_details.claim_number
        return await redirect_log_claim_with_query(claim_number, id_number, policy_number)

    covers_logger.warning("Will not try to add claimant bank details")
    return redirect(url_for('covers.add_claimant_bank_details', policy_number=policy_number,
                            claim_number=claimant_data.claim_number))


@covers_route.route('/covers/claims/log-claim-bank-details/<string:policy_number>/<string:claim_number>',
                    methods=["GET", "POST"])
@login_required
async def add_claimant_bank_details(user: User, policy_number: str, claim_number: str):
    """

    :param claim_number:
    :param user:
    :param policy_number:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    context = dict(user=user)
    if request.method.casefold() == "get":

        bank_id = request.args.get('bank_id')

        if bank_id:
            bank_details = await company_controller.get_bank_account(bank_account_id=bank_id)
            if isinstance(bank_details, BankAccount):
                context.update(old_bank_account=bank_details)

        claim_data = await covers_controller.get_claim_data(claim_number=claim_number)
        if claim_data:
            context.update(claim_data=claim_data)

        claimant_data = await covers_controller.get_claimant_data(claim_number=claim_number)
        if claimant_data:
            context.update(claimant_data=claimant_data)

        account_types = AccountTypes.account_types()
        context.update(policy_number=policy_number, claim_number=claim_number, account_types=account_types)

        if claimant_data.bank_id:
            old_bank_data = await company_controller.get_bank_account(bank_account_id=claimant_data.bank_id)
            context.update(old_bank_account=old_bank_data)

        if claim_data.member_id_number:
            client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
                id_number=claim_data.member_id_number)
            if client_data:
                context.update(client_data=client_data)

        covers_logger.info(context)
        return render_template('claims/sections/claimant_data.html', **context)

    # Employee Submitting Bank Account Details
    try:
        bank_details = BankAccount(**request.form)
    except ValidationError as e:
        covers_logger.warning(str(e))
        flash(message="Unable to add Bank details please ensure all your details are correct", category="danger")
        return redirect(url_for('covers.add_claimant_bank_details', policy_number=policy_number,
                                claim_number=claim_number))

    covers_logger.info(f"Bank Account Data: {bank_details}")
    bank_account: BankAccount = await company_controller.add_bank_account(bank_account=bank_details)
    if not isinstance(bank_account, BankAccount):
        flash(message="Unable to add Bank details please ensure all your details are correct", category="danger")
        return redirect(url_for('covers.add_claimant_bank_details', policy_number=policy_number,
                                claim_number=claim_number))

    # We will load the saved bank details on the next step
    _ = await covers_controller.update_claimant_bank_account_id(bank_account_id=bank_account.bank_account_id,
                                                                claim_number=claim_number)

    flash(message="Bank details updated now attach official documentations", category="success")
    return redirect(url_for('covers.attach_official_documentation', policy_number=policy_number,
                            claim_number=claim_number))


@covers_route.route('/covers/claims/log-claim-docs/<string:policy_number>/<string:claim_number>',
                    methods=["GET", "POST"])
@login_required
async def attach_official_documentation(user: User, policy_number: str, claim_number: str):
    """

    :param user:
    :param policy_number:
    :param claim_number:
    :return:
    """
    context = dict(user=user)
    claim_data = await covers_controller.get_claim_data(claim_number=claim_number)
    if not claim_data:
        flash("Invalid claim number.", "danger")
        return redirect(url_for('covers.log_claim', policy_number=policy_number, claim_number=claim_number))

    context.update(claim_data=claim_data)

    claimant_data = await covers_controller.get_claimant_data(claim_number=claim_number)
    if not claimant_data:
        flash("Invalid claim number.", "danger")
        return redirect(url_for('covers.log_claim', policy_number=policy_number, claim_number=claim_number))

    context.update(claimant_data=claimant_data)

    if claimant_data.bank_id:
        bank_account = await company_controller.get_bank_account(bank_account_id=claimant_data.bank_id)
        context.update(bank_account=bank_account)

    if claim_data.member_id_number:
        client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
            id_number=claim_data.member_id_number)
        if client_data:
            context.update(client_data=client_data)

    if request.method.casefold() == "get":

        claims_upload_folder_path = claims_upload_folder(company_id=claim_data.company_id,
                                                         claim_number=claimant_data.claim_number)
        existing_claim_files = []

        if claims_upload_folder_path:
            existing_claim_files = load_claims_files_in_folder(folder_path=claims_upload_folder_path)

        if existing_claim_files:
            context.update(claim_files=existing_claim_files)

        context.update(policy_number=policy_number, claim_number=claim_number)
        return render_template('claims/sections/claimant_data.html', **context)

    files = request.files.getlist('claim_documents')

    claims_upload_folder_path = claims_upload_folder(company_id=claim_data.company_id, claim_number=claim_number)
    saved_files = save_files_to_folder(folder_path=claims_upload_folder_path, file_list=files)

    option_success = (f"Successfully uploaded {len(saved_files)} document(s).", "success")
    option_failure = ("No valid files were uploaded.", "danger")
    message, cat = option_success if saved_files else option_failure
    flash(message=message, category=cat)

    return redirect(url_for('covers.retrieve_claim_status', claim_number=claim_number))


@covers_route.get('/covers/claims-status/<string:claim_number>')
@login_required
async def retrieve_claim_status(user: User, claim_number: str):
    """
    Retrieve and display all claim-related information including claimant details, bank account details,
    and uploaded files.

    :param user: Logged-in user.
    :param claim_number: Claim number to retrieve details for.
    :return: Rendered HTML template with claim status information.
    """
    # Ensure user is authorized to view this information
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result
    # TODO Consider verifying that the user can access this claim status
    # Retrieve claim data
    claim_data = await covers_controller.get_claim_data(claim_number=claim_number)

    claimant_data = await covers_controller.get_claimant_data(claim_number=claim_number)

    bank_account = await company_controller.get_bank_account(
        bank_account_id=claimant_data.bank_id) if claimant_data and claimant_data.bank_id else None

    # Load uploaded files
    claims_upload_folder_path = claims_upload_folder(company_id=claim_data.company_id, claim_number=claim_number)

    existing_claim_files = load_claims_files_in_folder(
        folder_path=claims_upload_folder_path) if claims_upload_folder_path else []

    client_data: ClientPersonalInformation = await company_controller.get_client_data_with_id_number(
        id_number=claim_data.member_id_number)

    # Prepare context for rendering
    context = {
        'claim_data': claim_data,
        'claimant_data': claimant_data,
        'bank_account': bank_account,
        'claim_files': existing_claim_files,
        'client_data': client_data,
        'user': user
    }

    # Render the template with the claim information
    return render_template('claims/claim_status.html', **context)


@covers_route.get('/covers/logged-claims')
@login_required
async def logged_claims(user: User):
    """

    :param user:
    :return:
    """
    # Ensure user is authorized to view this information
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    claims = await covers_controller.get_company_claims(company_id=user.company_id)
    context = dict(user=user, claims=claims)
    return render_template("claims/logged_claims.html", **context)
