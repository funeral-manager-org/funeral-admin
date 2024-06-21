from flask import Blueprint, render_template

from src.main import subscriptions_controller
from src.authentication import admin_login
from src.database.models.users import User
from src.logger import init_logger

billing_route = Blueprint('billing', __name__)
error_logger = init_logger('billing_logger')


@billing_route.get('/admin/billing')
@admin_login
async def get_billing(user: User):
    """

    :param user:
    :return:
    """
    if not user.company_id:
        pass

    subscription = await subscriptions_controller.get_company_subscription(company_id=user.company_id)
    if not subscription:
        subscription = {}

    context = dict(user=user, subscription=subscription)
    return render_template('billing/billing.html', **context)



