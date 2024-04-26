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
    context = dict(user=user, branches=company_branches)
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
    except ValidationError as e:
        print(str(e))

    flash(message="successfully created plan", category="success")
    return redirect(url_for('covers.get_covers'))

