from flask import Blueprint, render_template, url_for, flash, redirect, request

from src.authentication import login_required
from src.database.models.users import User
from src.main import company_controller

policy_route = Blueprint('policy', __name__)


@policy_route.get('/admin/employees/policies')
@login_required
async def get_policies_home(user: User):
    """

        :param user:
        :return:
    """
    policies_list = await company_controller.return_all_active_company_policies()
    outstanding_policies = await company_controller.return_all_outstanding_company_policies()
    context = dict(user=user, policies_list=policies_list, outstanding_policies=outstanding_policies)
    return render_template('admin/policies/policies.html', **context)


@policy_route.get('/admin/policies/search')
@login_required
async def get_search_policies(user: User):
    """

        :param user:
        :return:
    """

    context = dict(user=user)
    return render_template('admin/policies/paged/search_policies.html', **context)


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

    context = dict(user=user,page=0, count=25, policies_list=policies_list)
    # Render template with search results
    return render_template('admin/policies/search_results.html', **context)


@policy_route.get('/admin/policies/active/<int:page>/<int:count>')
@login_required
async def get_active_policies_paged(user: User, page: int = 0, count: int = 25):
    """

    :param user:
    :param page:
    :param count:
    :return:
    """
    if not user.company_id:
        flash(message="No Registered Funeral Company", category="danger")
        return redirect(url_for('policy.get_policies_home'))

    policies_list = await company_controller.return_all_active_company_policies_paged(company_id=user.company_id,
                                                                                      page=page, count=count)
    context = dict(user=user, page=page, count=count, policies_list=policies_list)
    return render_template('admin/policies/paged/active_policies.html', **context)


@policy_route.get('/admin/policies/lapsed/<int:page>/<int:count>')
@login_required
async def get_lapsed_policies_paged(user: User, page: int = 0, count: int = 25):
    """

    :param user:
    :param page:
    :param count:
    :return:
    """
    if not user.company_id:
        flash(message="No Registered Funeral Company", category="danger")
        return redirect(url_for('policy.get_policies_home'))

    policies_list = await company_controller.return_all_lapsed_company_policies_paged(company_id=user.company_id,
                                                                                      page=page, count=count)
    context = dict(user=user, page=page, count=count, policies_list=policies_list)
    return render_template('admin/policies/paged/lapsed_policies.html', **context)
