from flask import Blueprint, render_template, url_for, flash, redirect, request

from src.authentication import login_required
from src.database.models.users import User
from src.main import company_controller

policy_route = Blueprint('policy', __name__)


@policy_route.get('/admin/employees/policies')
@login_required
async def get_policies(user: User):
    """

        :param user:
        :return:
    """
    policies_list = await company_controller.return_all_active_company_policies()
    outstanding_policies = await company_controller.return_all_outstanding_company_policies()
    context = dict(user=user, policies_list=policies_list, outstanding_policies=outstanding_policies)
    return render_template('admin/policies/policies.html', **context)


@policy_route.post('/admin/employees/policies/search')
@login_required
async def search_policies(user: User):
    # Get form data
    search_option = request.form.get("search-option")
    search_input = request.form.get("search-input")

    # Perform search based on selected option
    if search_option == "id_number":
        # Perform search by ID Number
        policies_list = await company_controller.search_policies_by_id_number(search_input)
    elif search_option == "policy_number":
        # Perform search by Policy Number
        policies_list = await company_controller.search_policies_by_policy_number(search_input)
    elif search_option == "policy_holder_name":
        # Perform search by Policy Holder Name
        policies_list = await company_controller.search_policies_by_policy_holder_name(search_input)
    else:
        # Invalid search option
        flash("Invalid search option", "error")
        return redirect(url_for('policy.policies'))

    if policies_list:
        flash(message="policies found", category="success")
    else:
        flash(message="Unable to find the policies specified", category="success")
    print(policies_list)
    context = dict(user=user, policies_list=policies_list)
    # Render template with search results
    return render_template('admin/policies/search_results.html', **context)


