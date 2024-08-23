from datetime import datetime
from random import randint

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.logger import init_logger
from src.database.models.companies import EmployeeDetails, CompanyBranches
from src.database.models.messaging import SMSCompose, RecipientTypes, EmailCompose, SMSInbox, SMSSettings
from src.database.models.covers import ClientPersonalInformation
from src.authentication import login_required
from src.database.models.users import User
from src.main import company_controller, messaging_controller, subscriptions_controller
from src.utils import create_id

messaging_route = Blueprint('messaging', __name__)
messaging_logger = init_logger("messaging_logger")


@messaging_route.get('/admin/administrator/cloudflare')
@login_required
async def get_cloudflare(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/cloudflare.html', **context)


@messaging_route.get('/admin/administrator/messaging/top-up')
@login_required
async def get_topup(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/topup.html', **context)


@messaging_route.get('/admin/administrator/messaging/settings')
@login_required
async def get_admin(user: User):
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    context = dict(user=user)
    return render_template('admin/managers/messaging/settings.html', **context)


@messaging_route.post('/admin/administrator/messaging/sms-settings')
@login_required
async def update_sms_settings(user: User):
    """

    :param user:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    try:
        settings = SMSSettings(**request.form, company_id=user.company_id)
    except ValidationError as e:
        messaging_logger.error(str(e))
        flash(message="please provide all required sms settings", category="danger")
        return redirect(url_for('messaging.get_admin'))

    updated_settings = await messaging_controller.sms_service.add_sms_settings(settings=settings)

    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.post('/admin/administrator/messaging/whatsapp-settings')
@login_required
async def update_whatsapp_settings(user: User):
    """

    :param user:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


def create_fake_cell(length: int = 10) -> str:
    """
    Generate a fake cell number.

    :param length: Length of the cell number (default is 10)
    :return: Fake cell number
    """

    return ''.join([str(randint(0, 9)) for _ in range(length)])


def create_fake_sms_data(to_branch: str, message: str, count: int = 10) -> list[SMSInbox]:
    """
    **create_fake_sms_data**
    Generate fake SMSInbox data for testing.

    :param to_branch: Branch ID
    :param message: Message content
    :param count: Number of SMSInbox instances to generate (default is 10)
    :return: List of SMSInbox instances
    """
    sms_data = []
    for _ in range(count):
        sms_data.append(SMSInbox(
            from_cell=create_fake_cell(),
            to_branch=to_branch,
            message=message,
            is_read=bool(randint(0, 1)),  # Randomly set is_read to True or False
        ))
    return sms_data


async def get_sent_email_paged(user: User, branch_id: str, index: int, count: int = 25):
    """

    :param branch_id:
    :param user:
    :param index:
    :param count:
    :return:
    """
    return await messaging_controller.email_service.get_sent_messages(branch_id=branch_id)


async def get_sent_sms_paged(user: User, branch_id: str, index: int, count: int = 25):
    """

    :param branch_id:
    :param user:
    :param index:
    :param count:
    :return:
    """
    return await messaging_controller.sms_service.get_sent_box_messages_paged(branch_id=branch_id)


@messaging_route.get('/admin/administrator/messaging/inbox')
@login_required
async def get_inbox(user: User):
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    sms_inbox = await messaging_controller.get_sms_inbox(branch_id=user.branch_id)
    if not sms_inbox:
        # Generate at least ten fake SMS records for testing
        sms_inbox = create_fake_sms_data(to_branch="branch_id", message="Test message", count=10)

    context = dict(user=user, sms_inbox=sms_inbox)
    return render_template('admin/managers/messaging/inbox.html', **context)


@messaging_route.get('/admin/administrator/messaging/read-sms')
@login_required
async def read_sms_message(user: User, message_id: str):
    """

    :param user:
    :param message_id:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    context = dict(user=user)
    sms_inbox: list[SMSInbox] = await messaging_controller.get_sms_inbox(branch_id=user.branch_id)
    for sms in sms_inbox:
        if sms.message_id == message_id:
            context.update(sms=sms)
            return render_template("admin/managers/messaging/read_sms.html", **context)


@messaging_route.post('/admin/messaging/sms-sent/<int:page>/<int:count>')
@login_required
async def get_sent_sms_paged(user: User, page: int = 0, count: int = 25):
    """
        need to page the retrieval
    :param user:
    :param page:
    :param count:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    branch_id = request.form.get('branch_id')
    print(request.form)
    branches: list[CompanyBranches] = await company_controller.get_company_branches(company_id=user.company_id)

    if not branches:
        return redirect(url_for('messaging.get_admin'))

    if not branch_id:
        branch_id = branches[-1].branch_id

    sms_messages: list[SMSCompose] = await messaging_controller.sms_service.get_sent_box_messages_paged(
        branch_id=branch_id, page=page, count=count)

    context = dict(user=user, sms_messages=sms_messages, branches=branches, page=page, count=count, branch_id=branch_id)

    return render_template('admin/managers/messaging/paged/sms_sent.html', **context)


@messaging_route.get('/admin/messaging/sms-sent/<int:page>/<int:count>')
@login_required
async def get_sent_sms(user: User, page: int = 0, count: int = 25):
    """
        need to page the retrieval
    :param user:
    :param page:
    :param count:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    branches: list[CompanyBranches] = await company_controller.get_company_branches(company_id=user.company_id)
    if not branches:
        return redirect(url_for('messaging.get_admin'))

    branch_id = branches[-1].branch_id
    sms_messages: list[SMSCompose] = await messaging_controller.sms_service.get_sent_box_messages_paged(
        branch_id=branch_id, page=page, count=count)

    context = dict(user=user, sms_messages=sms_messages, branches=branches,
                   page=page, count=count, branch_id=branch_id)

    return render_template('admin/managers/messaging/paged/sms_sent.html', **context)


@messaging_route.get('/admin/messaging/email-sent/<int:page>/<int:count>')
@login_required
async def get_sent_email(user: User, page: int = 0, count: int = 25):
    """

    :param user:
    :param page:
    :param count:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    branches: list[CompanyBranches] = await company_controller.get_company_branches(company_id=user.company_id)
    if not branches:
        return redirect(url_for('messaging.get_admin'))

    branch_id = branches[-1].branch_id
    email_messages: list[EmailCompose] = await messaging_controller.email_service.get_sent_email_paged(
        branch_id=branch_id, page=page, count=count)
    context = dict(user=user, email_messages=email_messages, branches=branches, page=page, count=count,
                   branch_id=branch_id)

    return render_template('admin/managers/messaging/paged/email_sent.html', **context)


@messaging_route.route('/admin/messaging/email-sent/<string:branch_id>/<int:page>/<int:count>', methods=['GET', 'POST'])
@login_required
async def post_sent_email_paged(user: User, branch_id: str, page: int = 0, count: int = 25):
    """

    :param user:
    :param page:
    :param count:
    :param branch_id:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    branch_id: str = request.form.get('branch_id', branch_id)

    branches: list[CompanyBranches] = await company_controller.get_company_branches(company_id=user.company_id)
    if not branches:
        return redirect(url_for('messaging.get_admin'))
    if not branch_id:
        branch_id = branches[-1].branch_id

    email_messages: list[EmailCompose] = await messaging_controller.email_service.get_sent_email_paged(
        branch_id=branch_id, page=page, count=count)
    context = dict(user=user, email_messages=email_messages, branches=branches, page=page, count=count,
                   branch_id=branch_id)

    return render_template('admin/managers/messaging/paged/email_sent.html', **context)


# ---------------compose

@messaging_route.get('/admin/messaging/email/compose')
@login_required
async def get_email_compose(user: User):
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    recipient_list: list[str] = RecipientTypes.get_fields()
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches, recipient_list=recipient_list)
    return render_template('admin/managers/messaging/paged/compose/email.html', **context)


@messaging_route.get('/admin/messaging/sms/compose')
@login_required
async def get_sms_compose(user: User):
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    recipient_list: list[str] = RecipientTypes.get_fields()
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches, recipient_list=recipient_list)
    return render_template('admin/managers/messaging/paged/compose/sms.html', **context)


@messaging_route.get('/admin/messaging/outbox/<string:message_id>')
@login_required
async def get_outbox_email_message(user: User, message_id: str):
    """

    :param user:
    :param message_id:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    sent_message: EmailCompose = await messaging_controller.email_service.get_sent_email(message_id=message_id)
    context = dict(user=user, message=sent_message)
    return render_template('admin/managers/messaging/message.html', **context)


async def send_sms_to_branch_policy_holders(composed_sms: SMSCompose, user: User):
    """
        # TODO investigate how to run this as a separate thread and just respond to user separately
        will send sms to branch policy holders
    :param composed_sms:
    :return:
    """
    # Obtain Policy Holders in Branch
    branch_clients = await company_controller.get_branch_policy_holders(branch_id=composed_sms.to_branch)
    # Use The Contact ID's to obtain the Contact Records from database
    contact_list = [await company_controller.get_contact(contact_id=contact_id)
                    for contact_id in [client.contact_id for client in branch_clients if client.contact_id]]
    # Obtain Cell Number from each Contact Record where there is a Cell Number
    recipient_list = [contact.cell for contact in contact_list if contact.cell]
    # For Every Cell Number Send a Message - this will insert the message into the out message Queue
    if not await subscriptions_controller.subscription_can_send_sms(user=user, email_count=len(recipient_list)):
        message: str = f"""Cannot Send {len(recipient_list)} SMS's as you do not have enough sms credits available 
        please buy an extra sms package"""
        flash(message=message, category="danger")
        return redirect(url_for('messaging.get_topup'))

    for cell in recipient_list:
        sms = SMSCompose(to_cell=cell, message=composed_sms.message, to_branch=composed_sms.to_branch,
                         recipient_type=composed_sms.recipient_type)
        is_sent = await messaging_controller.send_sms(composed_sms=sms)
        print(f"is SMS Sent : {is_sent}")

        # on the Queue after its delivered we can update the message delivered on the local database


async def send_sms_to_branch_employees(composed_sms: SMSCompose, user: User):
    """
        # TODO investigate how to run this as a separate thread and just respond to user separately

        will send sms to branch_employees
    :param composed_sms:
    :return:
    """
    branch_employees = await company_controller.get_branch_employees(branch_id=composed_sms.to_branch)
    employees_contact_numbers = set()

    if not await subscriptions_controller.subscription_can_send_sms(user=user, email_count=len(branch_employees)):
        message: str = f"""Cannot Send {len(branch_employees)} SMS's as you do not have enough sms credits available 
        please buy an extra sms package"""
        flash(message=message, category="danger")
        return redirect(url_for('messaging.get_topup'))

    for employee in branch_employees:
        # Check if the employee has a contact number
        # If not, but has a contact ID, get the contact's cell number
        if employee.contact_id:
            # Fetch contact details
            contact = await company_controller.get_contact(contact_id=employee.contact_id)
            # Extract cell numbers from contacts
            employees_contact_numbers.add(contact.cell)

        elif employee.contact_number:
            employees_contact_numbers.add(employee.contact_number)

    # Send SMS to each employee's contact number
    for cell in employees_contact_numbers:
        sms = SMSCompose(message=composed_sms.message, to_cell=cell, to_branch=composed_sms.to_branch,
                         recipient_type=composed_sms.recipient_type)
        is_sent = await messaging_controller.send_sms(composed_sms=sms)
        # TODO - we can start updating the local database showing the sms was sent
        # on the Queue after its delivered we can update the message delivered on the local database


async def send_sms_to_branch_lapsed_policy_holders(composed_sms: SMSCompose, user: User):
    """
        # TODO investigate how to run this as a separate thread and just respond to user separately

    :param composed_sms:
    :return:
    """
    lapsed_policy_holders: list[
        ClientPersonalInformation] = await company_controller.get_branch_policy_holders_with_lapsed_policies(
        branch_id=composed_sms.to_branch)
    policy_holder_contact_numbers = set()

    if not await subscriptions_controller.subscription_can_send_sms(user=user, email_count=len(lapsed_policy_holders)):
        message: str = f"""Cannot Send {len(lapsed_policy_holders)} SMS's as you do not have enough sms credits available 
        please buy an extra sms package"""
        flash(message=message, category="danger")
        return redirect(url_for('messaging.get_topup'))

    for policy_holder in lapsed_policy_holders:
        if policy_holder.contact_id:
            # Fetch contact details
            contact = await company_controller.get_contact(contact_id=policy_holder.contact_id)
            # Extract cell numbers from contacts
            policy_holder_contact_numbers.add(contact.cell)

    for cell in policy_holder_contact_numbers:
        sms = SMSCompose(to_cell=cell, message=composed_sms.message, to_branch=composed_sms.to_branch,
                         recipient_type=composed_sms.recipient_type)
        is_sent = await messaging_controller.send_sms(composed_sms=sms)


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@messaging_route.post('/admin/messaging/sms/compose')
@login_required
async def send_composed_sms_message(user: User):
    """
        processes both managers and employees compose message
        will redirect to the compose of employee or manager upon completion
    :param user:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    try:
        composed_sms = SMSCompose(**request.form)

    except ValidationError as e:
        print(str(e))
        flash(message="Error sending SMS please ensure to fill in the form", category="danger")
        return redirect(url_for('messaging.get_sms_compose'))

    if composed_sms.recipient_type.casefold() == RecipientTypes.EMPLOYEES.value.casefold():
        # Could Be interesting to just send this to a separate thread

        await send_sms_to_branch_employees(composed_sms=composed_sms, user=user)

    elif composed_sms.recipient_type.casefold() == RecipientTypes.CLIENTS.value.casefold():
        await send_sms_to_branch_policy_holders(composed_sms=composed_sms, user=user)

    elif composed_sms.recipient_type.casefold() == RecipientTypes.LAPSED_POLICY.value.casefold():
        # Get policyholders with Lapsed Policies
        await send_sms_to_branch_lapsed_policy_holders(composed_sms=composed_sms, user=user)

    flash(message="Message Successfully sent", category="success")
    return redirect(url_for('messaging.get_sms_compose'))


# Sending Email Messages Routes
async def send_emails(composed_email: EmailCompose,
                      persons_list: list[ClientPersonalInformation | EmployeeDetails]) -> bool:
    for person in persons_list:
        if person.contact_id:
            contact = await company_controller.get_contact(contact_id=person.contact_id)
            if contact.email:
                email = EmailCompose(to_email=contact.email, to_branch=composed_email.to_branch,
                                     message=composed_email.message, subject=composed_email.subject,
                                     recipient_type=composed_email.recipient_type)
                await messaging_controller.send_email(email=email)
        elif person.email:
            email = EmailCompose(to_email=person.email, to_branch=composed_email.to_branch,
                                 message=composed_email.message, subject=composed_email.subject,
                                 recipient_type=composed_email.recipient_type)
            await messaging_controller.send_email(email=email)

    return True


@messaging_route.post('/admin/messaging/email/compose')
@login_required
async def send_email_message(user: User):
    """

    :param user:
    :return:
    """
    result = await subscriptions_controller.route_guard(user=user)
    if result:
        return result

    try:
        composed_email = EmailCompose(**request.form)
    except ValidationError as e:
        print(str(e))
        flash(message="Error sending SMS please ensure to fill in the form", category="danger")
        return redirect(url_for('messaging.get_email_compose'))

    if composed_email.recipient_type == RecipientTypes.EMPLOYEES.value:

        branch_employees: list[EmployeeDetails] = await company_controller.get_branch_employees(
            branch_id=composed_email.to_branch)

        if not await subscriptions_controller.subscription_can_send_emails(user=user, email_count=len(branch_employees)):
            message: str = f"""Cannot Send {len(branch_employees)} Emails as you do not have enough email credits available 
            please buy an email package"""
            flash(message=message, category="danger")
            return redirect(url_for('messaging.get_topup'))

        await send_emails(composed_email=composed_email, persons_list=branch_employees)

    elif composed_email.recipient_type == RecipientTypes.CLIENTS.value:

        policy_holders: list[ClientPersonalInformation] = await company_controller.get_branch_policy_holders(
            branch_id=composed_email.to_branch)

        if not await subscriptions_controller.subscription_can_send_emails(user=user, email_count=len(policy_holders)):
            message: str = f"""Cannot Send {len(policy_holders)} Emails,  as you do not have enough email credits available 
            please buy an email package"""
            flash(message=message, category="danger")
            return redirect(url_for('messaging.get_topup'))

        await send_emails(composed_email=composed_email, persons_list=policy_holders)

    elif composed_email.recipient_type == RecipientTypes.LAPSED_POLICY.value:
        # obtaining policyholders with lapsed policies
        policy_holders = await company_controller.get_branch_policy_holders_with_lapsed_policies(
            branch_id=composed_email.to_branch)

        if not await subscriptions_controller.subscription_can_send_emails(user=user, email_count=len(policy_holders)):
            message: str = f"""Cannot Send {len(policy_holders)} Emails,  as you do not have enough email credits available 
            please buy an email package"""
            flash(message=message, category="danger")
            return redirect(url_for('messaging.get_topup'))

        await send_emails(composed_email=composed_email, persons_list=policy_holders)
    else:
        flash(message="Could Not Send Email Message", category="success")
        return redirect(url_for('messaging.get_email_compose'))

    flash(message="Successfully sent email message", category="success")
    return redirect(url_for('messaging.get_email_compose'))
