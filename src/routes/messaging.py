from flask import Blueprint, render_template, url_for, flash, redirect, request

from src.database.models.messaging import SMSCompose, RecipientTypes
from src.database.models.covers import ClientPersonalInformation
from src.authentication import login_required
from src.database.models.users import User
from src.main import company_controller, messaging_controller

messaging_route = Blueprint('messaging', __name__)


@messaging_route.get('/admin/administrator/cloudflare')
@login_required
async def get_cloudflare(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/cloudflare.html', **context)


@messaging_route.get('/admin/administrator/messaging/topup')
@login_required
async def get_topup(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/topup.html', **context)


@messaging_route.get('/admin/administrator/messaging/settings')
@login_required
async def get_admin(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/settings.html', **context)


@messaging_route.post('/admin/administrator/messaging/sms-settings')
@login_required
async def update_sms_settings(user: User):
    """

    :param user:
    :return:
    """
    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.post('/admin/administrator/messaging/whatsapp-settings')
@login_required
async def update_whatsapp_settings(user: User):
    """

    :param user:
    :return:
    """

    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.get('/admin/administrator/messaging/inbox')
@login_required
async def get_inbox(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/inbox.html', **context)


@messaging_route.get('/admin/administrator/messaging/sent')
@login_required
async def get_sent(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/sent.html', **context)


@messaging_route.get('/admin/administrator/messaging/compose')
@login_required
async def get_compose(user: User):
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches)
    return render_template('admin/managers/messaging/compose.html', **context)


@messaging_route.get('/admin/employees/messaging/inbox')
@login_required
async def get_employee_inbox(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/inbox.html', **context)


@messaging_route.get('/admin/employees/messaging/sent')
@login_required
async def get_employee_sent(user: User):
    context = dict(user=user)
    return render_template('admin/managers/messaging/sent.html', **context)


@messaging_route.get('/admin/employees/messaging/compose')
@login_required
async def get_employee_compose(user: User):
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches)
    return render_template('admin/managers/messaging/compose.html', **context)


#################################################################################################

async def send_sms_to_branch_policy_holders(composed_sms):
    # Obtain Policy Holders in Branch
    branch_clients = await company_controller.get_branch_policy_holders(branch_id=composed_sms.to_branch)
    # Use The Contact ID's to obtain the Contact Records from database
    contact_list = [await company_controller.get_contact(contact_id=contact_id)
                    for contact_id in [client.contact_id for client in branch_clients if client.contact_id]]
    # Obtain Cell Number from each Contact Record where there is a Cell Number
    recipient_list = [contact.cell for contact in contact_list if contact.cell]
    # For Every Cell Number Send a Message - this will insert the message into the out message Queue
    for cell in recipient_list:
        await messaging_controller.send_sms(recipient=cell, message=composed_sms.message)


async def send_sms_to_branch_employees(composed_sms):
    branch_employees = await company_controller.get_branch_employees(branch_id=composed_sms.to_branch)
    employees_contact_numbers = []
    for employee in branch_employees:
        # Check if the employee has a contact number
        if employee.contact_number:
            employees_contact_numbers.append(employee.contact_number)
        # If not, but has a contact ID, get the contact's cell number
        elif employee.contact_id:
            # Fetch contact details
            contact = await company_controller.get_contact(contact_id=employee.contact_id)
            # Extract cell numbers from contacts
            employees_contact_numbers.append(contact.cell)
    # Send SMS to each employee's contact number
    for cell in employees_contact_numbers:
        await messaging_controller.send_sms(recipient=cell, message=composed_sms.message)


async def create_response(user: User):
    if user.is_employee and not user.is_company_admin:
        flash(message="Message Successfully sent", category="success")
        return redirect(url_for('messaging.get_employee_compose'))

    # This will return company admin compose
    flash(message="Message Successfully sent", category="success")
    return redirect(url_for('messaging.get_compose'))


@messaging_route.post('/admin/messaging/sms/compose')
@login_required
async def send_composed_sms_message(user: User):
    """
        processes both managers and employees compose message
        will redirect to the compose of employee or manager upon completion
    :param user:
    :return:
    """

    composed_sms = SMSCompose(**request.form)

    if composed_sms.recipient_type.casefold() == RecipientTypes.EMPLOYEES.value.casefold():
        await send_sms_to_branch_employees(composed_sms)

    elif composed_sms.recipient_type.casefold() == RecipientTypes.CLIENTS.value.casefold():
        await send_sms_to_branch_policy_holders(composed_sms)

    elif composed_sms.recipient_type.casefold() == RecipientTypes.LAPSED_POLICY.value.casefold():
        # Get Policy Holders with Lapsed Policies
        pass



    return await create_response(user=user)
