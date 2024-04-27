from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.database.models.companies import CoverPlanDetails
from src.main import company_controller
from src.database.models.covers import ClientPersonalInformation, PolicyRegistrationData
from src.authentication import login_required
from src.database.models.users import User

clients_route = Blueprint('clients', __name__)


@clients_route.get('/admin/employees/clients')
@login_required
async def get_clients(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    plan_covers = await company_controller.get_company_covers(company_id=user.company_id)
    policy_holders_list = await company_controller.get_policy_holders(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches, plan_covers=plan_covers,
                   policy_holders_list=policy_holders_list)

    return render_template('admin/clients/clients.html', **context)


@clients_route.post('/admin/employees/clients/new-clients')
@login_required
async def add_client(user: User):
    """

    :param user:
    :return:
    """
    try:
        policy_holder: ClientPersonalInformation = ClientPersonalInformation(**request.form)
        print(policy_holder)
    except ValidationError as e:
        print(str(e))
        flash(message="Unable to create or update client please provide all required details", category="danger")
        return redirect(url_for('clients.get_clients'))

    policy_holder = await company_controller.add_policy_holder(policy_holder=policy_holder)

    plan_cover: CoverPlanDetails = await company_controller.get_plan_cover(
        company_id=user.company_id, plan_number=policy_holder.plan_number)

    policy = PolicyRegistrationData(uid=policy_holder.uid,
                                    branch_id=policy_holder.branch_id,
                                    company_id=policy_holder.company_id,
                                    plan_number=policy_holder.plan_number,
                                    policy_type=plan_cover.plan_type,
                                    total_premiums=plan_cover.premium_costs)

    policy_ = await company_controller.add_policy_data(policy_data=policy)

    message = "Successfully created new client please remember to add family members"
    flash(message=message, category="success")
    return redirect(url_for('clients.get_clients'))




