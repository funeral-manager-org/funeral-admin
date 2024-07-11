from flask import Blueprint, render_template

from src.authentication import system_login
from src.database.models.companies import Company
from src.database.models.subscriptions import PlanNames, Subscriptions
from src.database.models.users import User
from src.logger import init_logger
from src.main import system_controller, company_controller

system_route = Blueprint('system', __name__)
error_logger = init_logger('System Router')


@system_route.get('/_system-admin/companies')
@system_login
async def get_companies(user: User):
    """

    :param user:
    :return:
    """

    company_list: list[Company] = await system_controller.get_all_companies()
    context = dict(user=user, company_list=company_list)

    return render_template('system/companies.html', **context)


@system_route.get('/_system-admin/company/<string:company_id>')
@system_login
async def get_company_details(user: User, company_id: str):
    """

    :param user:
    :return:
    """
    company_data = await company_controller.get_company_details(company_id=company_id)
    company_branches = await company_controller.get_company_branches(company_id=company_id)
    branch_details = {}
    for branch in company_branches:
        if branch.contact_id:
            contact = await company_controller.get_contact(contact_id=branch.contact_id)
        else:
            contact = {}
        if branch.postal_id:
            postal_address = await company_controller.get_postal_address(postal_id=branch.postal_id)
        else:
            postal_address = {}
        if branch.address_id:
            physical_address = await company_controller.get_address(address_id=branch.address_id)
        else:
            physical_address = {}
        if branch.bank_account_id:
            bank_account = await company_controller.get_bank_account(bank_account_id=branch.bank_account_id)
        else:
            bank_account = {}

        branch_details[branch.branch_id] = {
            'branch': branch,
            'contact': contact,
            'postal_address': postal_address,
            'physical_address': physical_address,
            'bank_account': bank_account
        }

    context = dict(user=user, company_data=company_data, branches=branch_details)

    return render_template('system/company_details.html', **context)


@system_route.get('/_system-admin/company/subscription/<string:company_id>')
@system_login
async def get_company_subscription(user: User, company_id: str):
    """

    :param user:
    :param company_id:
    :return:
    """
    company_data: Company = await company_controller.get_company_details(company_id=company_id)
    subscription_list: list[Subscriptions] = await system_controller.get_subscriptions(company_id=company_id)
    context = dict(user=user, company_data=company_data, subscription_list=subscription_list)

    return render_template('system/subscriptions/subscription_list.html', **context)


@system_route.get('/_system-admin/subscription/<string:subscription_id>')
@system_login
async def edit_subscription(user: User, subscription_id: str):
    """

    :param user:
    :param subscription_id:
    :return:
    """
    plan_names: list[str] = PlanNames.plan_names()
    subscription: Subscriptions = await system_controller.get_subscription(subscription_id=subscription_id)
    context = dict(user=user, subscription=subscription, plan_names=plan_names)
    return render_template('system/subscriptions/subscription.html', **context)


@system_route.post('/_system-admin/subscription/<string:subscription_id>')
@system_login
async def update_subscription(user: User, subscription_id: str):
    """

    :param user:
    :param subscription_id:
    :return:
    """
    pass

