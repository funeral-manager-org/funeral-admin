from flask import Blueprint, render_template, url_for, flash, redirect, request

from src.authentication import login_required
from src.database.models.companies import Company, CompanyBranches
from src.database.models.users import User
from src.main import company_controller, user_controller

company_route = Blueprint('company', __name__)


@company_route.get('/admin')
@login_required
async def get_admin(user: User):
    """

    :return:
    """
    context = dict(user=user)
    print(f"User : {user}")
    print(f"Company ID: {user.company_id}")
    if user.company_id:
        company_data = await company_controller.get_company_details(company_id=user.company_id)
        company_branches = await company_controller.get_company_branches(company_id=user.company_id)
        print(f" company : {company_data}")
    else:
        company_data = {}
        company_branches = []
    context.update(company=company_data, company_branches=company_branches)

    if user.is_system_admin:
        return render_template('admin/admin.html', **context)
    elif user.is_company_admin:
        return render_template('admin/managers/manager.html', **context)
    elif user.is_employee:
        return render_template('admin/employees/employee.html', **context)
    elif user.is_client:
        return render_template('admin/clients/clients.html', **context)

    flash(message="you are not a client in this portal consider applying for a cover in a funeral company near you",
          category='success')

    return redirect(url_for('home.get_home'))


@company_route.get('/admin/company/register')
@login_required
async def get_register(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('admin/tasks/company/register.html', **context)


@company_route.post('/admin/company/register')
@login_required
async def do_register(user: User):
    company_name = request.form.get('company_name')
    company_description = request.form.get('company_description')
    company_slogan = request.form.get('company_slogan')
    reg_ck = request.form.get('reg_ck')
    vat_number = request.form.get('vat_number')

    company = Company(reg_ck=reg_ck, vat_number=vat_number,
                      company_name=company_name,
                      company_slogan=company_slogan,
                      company_description=company_description,
                      admin_uid=user.uid)
    print(f"Company ID: {company.company_id}")
    registered_company = await company_controller.register_company(company=company)
    user.is_company_admin = True
    user.company_id = registered_company.company_id
    updated_user = await user_controller.put(user=user)
    flash(message="company successfully registered", category="success")
    # context = dict(user=updated_user, company_data=registered_company)
    return redirect(url_for('company.get_admin'))


@company_route.post('/admin/company/add-branch')
@login_required
async def add_company_branch(user: User):
    """

    :param user:
    :return:
    """
    company_branch = request.form.get('branch_name')
    company_description = request.form.get('branch_description')

    company_branch = CompanyBranches(company_id=user.company_id, branch_name=company_branch,
                                     branch_description=company_description)

    added_branch = await company_controller.add_company_branch(company_branch=company_branch)
    if not added_branch:
        flash(message="Error Adding New Branch - possibility is that the branch is already added", category="danger")
        return redirect(url_for('company.get_admin'))

    flash(message="branch successfully added", category="danger")
    return redirect(url_for('company.get_admin'))
