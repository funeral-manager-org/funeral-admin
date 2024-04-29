

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.models.bank_accounts import BankAccount
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.authentication import login_required
from src.database.models.companies import Company, CompanyBranches, EmployeeDetails, CoverPlanDetails
from src.database.models.users import User
from src.main import company_controller, user_controller, encryptor
from src.utils import create_id

messaging_route = Blueprint('messaging', __name__)




@messaging_route.get('/admin/administrator/cloudflare')
@login_required
async def get_cloudflare(user: User):

    return render_template('admin/managers/messaging/cloudflare.html')


@messaging_route.get('/admin/administrator/messaging/topup')
@login_required
async def get_topup(user: User):

    return render_template('admin/managers/messaging/topup.html')


@messaging_route.get('/admin/administrator/messaging/settings')
@login_required
async def get_admin(user: User):

    return render_template('admin/managers/messaging/settings.html')


@messaging_route.post('/admin/administrator/messaging/sms-settings')
@login_required
async def update_sms_settings(user:User):
    """

    :param user:
    :return:
    """
    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.post('/admin/administrator/messaging/whatsapp-settings')
@login_required
async def update_whatsapp_settings(user:User):
    """

    :param user:
    :return:
    """
    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.get('/admin/administrator/messaging/inbox')
@login_required
async def get_inbox(user: User):
    return render_template('admin/managers/messaging/inbox.html')


@messaging_route.get('/admin/administrator/messaging/sent')
@login_required
async def get_sent(user: User):
    return render_template('admin/managers/messaging/sent.html')

@messaging_route.get('/admin/administrator/messaging/compose')
@login_required
async def get_compose(user: User):
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches)
    return render_template('admin/managers/messaging/compose.html', **context)

