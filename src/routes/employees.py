from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.companies import EmployeeDetails
from src.database.models.users import User
from src.main import company_controller

employee_route = Blueprint('employees', __name__)


@employee_route.get('/admin/administrators/employees')
@login_required
async def get_employees(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    employees_list: list[EmployeeDetails] = await company_controller.get_company_employees(company_id=user.company_id)
    context = dict(user=user, employees_list=employees_list, branches=company_branches)
    return render_template("admin/managers/employees.html", **context)
