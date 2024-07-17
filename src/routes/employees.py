from flask import Blueprint, render_template

from src.authentication import login_required, admin_login
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


# noinspection DuplicatedCode
@employee_route.get('/admin/administrators/employee/<string:employee_id>')
@admin_login
async def get_employee_detail(user: User, employee_id: str):
    """
    **get_employee_detail**
    :param user:
    :param employee_id:
    :return:
    """
    employee_detail: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)

    context = dict(user=user, employee_detail=employee_detail)
    if employee_detail.contact_id:
        contact_details = await company_controller.get_contact(contact_id=employee_detail.contact_id)
        context.update(contact_details=contact_details)
    if employee_detail.address_id:
        physical_address = await company_controller.get_address(address_id=employee_detail.address_id)
        context.update(physical_address=physical_address)
    if employee_detail.postal_id:
        postal_address = await company_controller.get_postal_address(postal_id=employee_detail.postal_id)
        context.update(postal_address=postal_address)
    if employee_detail.bank_account_id:
        bank_account = await company_controller.get_bank_account(bank_account_id=employee_detail.bank_account_id)
        context.update(bank_account=bank_account)

    return render_template('admin/managers/employees/view.html', **context)
