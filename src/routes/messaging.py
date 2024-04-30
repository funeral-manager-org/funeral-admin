from flask import Blueprint, render_template, url_for, flash, redirect, request

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


@messaging_route.post('/admin/messaging/sms/compose')
@login_required
async def send_composed_sms_message(user: User):
    """
        processes both managers and employees compose message
        will redirect to the compose of employee or manager upon completion
    :param user:
    :return:
    """

    recipient_type = request.form.get('recipient_type')
    to_branch = request.form.get('to_branch')
    message = request.form.get('message')
    print(recipient_type, to_branch, message)

    if recipient_type.casefold() == "employee":
        branch_employees = await company_controller.get_branch_employees(branch_id=to_branch)
        print(f"Branch Emmployees = {branch_employees}")
    elif recipient_type.casefold() == "client":
        branch_clients: list[ClientPersonalInformation] = await company_controller.get_branch_policy_holders(
            branch_id=to_branch)
        recipient_list = [client.contact_id for client in branch_clients if client.contact_id]
        contact_list = [await company_controller.get_contact(contact_id=contact_id) for contact_id in recipient_list]
        recipient_list = [contact.cell for contact in contact_list]
        print(f"Branch Clients : {recipient_list}")
        for cell in recipient_list:
            is_sent = await messaging_controller.send_sms(recipient=cell, message=message)
            print(f"is Sent : {is_sent}")

    if user.is_employee:
        flash(message="Message Successfully sent", category="success")
        return redirect(url_for('messaging.get_employee_compose'))

    flash(message="Message Successfully sent", category="success")
    return redirect(url_for('messaging.get_compose'))
