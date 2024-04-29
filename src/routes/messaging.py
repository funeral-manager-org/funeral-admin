
from flask import Blueprint, render_template, url_for, flash, redirect

from src.authentication import login_required
from src.database.models.users import User
from src.main import company_controller

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
async def update_sms_settings(user :User):
    """

    :param user:
    :return:
    """
    flash(message="Successfully updated SMS Settings", category="success")
    return redirect(url_for('messaging.get_admin'))


@messaging_route.post('/admin/administrator/messaging/whatsapp-settings')
@login_required
async def update_whatsapp_settings(user :User):
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
