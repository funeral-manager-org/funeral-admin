from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.models.bank_accounts import BankAccount
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.authentication import login_required
from src.database.models.companies import Company, CompanyBranches, EmployeeDetails, CoverPlanDetails
from src.database.models.users import User
from src.main import company_controller, user_controller, encryptor
from src.utils import create_id

covers_route = Blueprint('covers', __name__)


@covers_route.get('/admin/administrator/covers')
@login_required
async def get_covers(user: User):
    """

        :param user:
        :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    cover_details = await company_controller.get_company_covers(company_id=user.company_id)
    context = dict(user=user, branches=company_branches, cover_details=cover_details)
    return render_template('admin/managers/covers.html', **context)


@covers_route.post('/admin/administrator/covers/add-plan-cover')
@login_required
async def add_plan_cover(user: User):
    """
        :param user:
        :return:
    """
    try:

        plan_cover = CoverPlanDetails(**request.form)
        print(plan_cover)
        plan_cover.company_id = user.company_id
    except ValidationError as e:
        print(str(e))
        flash(message="Unable to create plan please provide all necessary details", category="danger")
        return redirect(url_for('covers.get_covers'))

    updated_plan_cover = await company_controller.create_plan_cover(plan_cover=plan_cover)

    flash(message="successfully created plan", category="success")
    return redirect(url_for('covers.get_covers'))


@covers_route.get('/admin/administrator/cover/<string:company_id>/<string:plan_number>')
@login_required
async def get_plan_cover(user: User, company_id: str, plan_number: str):
    """

    :param user:
    :param company_id:
    :param plan_number:
    :return:
    """
    if user.company_id != company_id:
        flash(message="You are not authorized to view the cover details", category="danger")

        return redirect('home.get_home')

    plan_cover = await company_controller.get_plan_cover(company_id=company_id, plan_number=plan_number)
    context = dict(user=user, plan_cover=plan_cover)
    return render_template('admin/managers/covers/view.html', **context)

