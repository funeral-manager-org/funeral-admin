import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.database.models.bank_accounts import BankAccount
from src.authentication import login_required
from src.database.models.companies import EmployeeDetails, CompanyBranches, Salary
from src.database.models.contacts import Contacts, PostalAddress, Address
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, employee_controller

employee_route = Blueprint('employees', __name__)
employee_logger = init_logger('employee_route')


async def add_data_employee(context, employee_detail):
    if not employee_detail:
        return

    employee_logger.info(employee_detail)

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

    return context


@employee_route.get('/admin/employee-details')
@login_required
async def get_employee_details(user: User):
    """

    :param user:
    :return:
    """
    employee_logger.info(user)
    employee_logger.info(f"IS COMPANY ADMIN : {user.is_company_admin}")

    if not user.can_access_employee_record:
        message: str = "Please ensure that you are a company employee and have properly verified your email account"
        flash(message=message, category="danger")
        return redirect(url_for('home.get_home'))

    employee_roles: list[str] = await employee_controller.get_roles()
    country_list: list[str] = await company_controller.get_countries()
    context: dict[str, list[str] | User | EmployeeDetails | Salary] = dict(
        user=user, employee_roles=employee_roles, country_list=country_list)
    employee_detail: EmployeeDetails | None = None
    employee_detail = await employee_controller.get_employee_complete_details_uid(uid=user.uid)
    employee_logger.info(f"COMPARED TO THIS : {employee_detail}")
    if employee_detail:
        # this adds postal addresses and others

        context = await add_data_employee(context=context, employee_detail=employee_detail)
        salary_detail: Salary = await employee_controller.get_salary_details(employee_id=employee_detail.employee_id)
        context.update(salary_detail=salary_detail)
        context.update(employee_detail=employee_detail)
    # return render_template('admin/managers/employees/view.html', **context)
    return render_template('admin/employees/employee.html', **context)


@employee_route.post('/admin/employee-details/update')
@login_required
async def update_employee_details(user: User):
    """

    :param user:
    :return:
    """
    employee_details: EmployeeDetails = EmployeeDetails(**request.form, uid=user.uid)
    employee_logger.info(f"Employee Logger : {employee_details}")
    if user.branch_id:
        employee_details.branch_id = user.branch_id
    if user.company_id:
        employee_details.company_id = user.company_id

    employee_logger.info(employee_details)
    employee = await employee_controller.add_update_employee_details(employee_details=employee_details)

    if not isinstance(employee, EmployeeDetails):
        flash(message="Unable to update employee details", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    flash(message="successfully updated employee details", category="success")
    return redirect(url_for('employees.get_employee_details'))


@employee_route.post('/admin/employee-details/update-contacts')
@login_required
async def update_contact_details(user: User):
    """

    :param user:
    :return:
    """
    try:
        contact_details: Contacts = Contacts(**request.form)

    except ValidationError as e:
        employee_logger.error(str(e))
        flash(message="unable to add contact details to employee", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details: EmployeeDetails = await company_controller.get_employee_by_uid(uid=user.uid)
    if not isinstance(employee_details, EmployeeDetails):
        flash(message="Employee details not found please try again later", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    contact = await company_controller.add_contacts(contact=contact_details)

    if not isinstance(contact, Contacts):
        flash(message="could not add or update contact details please try again later", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details.contact_id = contact.contact_id
    employee_logger.info(f'Contact ID: {contact}')
    employee: EmployeeDetails = await employee_controller.add_update_employee_details(employee_details=employee_details)

    if not isinstance(employee, EmployeeDetails):
        flash(message="unable to add contact details to employee", category="danger")

    flash(message="successfully updated employee details", category="success")
    return redirect(url_for('employees.get_employee_details'))


@employee_route.post('/admin/employee-details/update-postal')
@login_required
async def update_postal_address(user: User):
    """

    :param user:
    :return:
    """
    try:
        postal_details: PostalAddress = PostalAddress(**request.form)

    except ValidationError as e:

        employee_logger.error(str(e))
        flash(message="unable to add postal address to employee", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details: EmployeeDetails = await company_controller.get_employee_by_uid(uid=user.uid)
    if not isinstance(employee_details, EmployeeDetails):
        flash(message="Employee details not found please try again later", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    postal_address: PostalAddress = await company_controller.add_postal_address(postal_address=postal_details)

    if not isinstance(postal_address, PostalAddress):
        flash(message="could not add/update postal address", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details.postal_id = postal_address.postal_id
    employee = await employee_controller.add_update_employee_details(employee_details=employee_details)

    if not isinstance(employee, EmployeeDetails):
        flash(message="unable to add/update postal address to employee", category="danger")

    flash(message="successfully updated employee details", category="success")
    return redirect(url_for('employees.get_employee_details'))


@employee_route.post('/admin/employee-details/update-physical')
@login_required
async def update_physical_address(user: User):
    """

    :param user:
    :return:
    """
    try:
        physical_address: Address = Address(**request.form)
    except ValidationError as e:
        employee_logger.error(str(e))
        flash(message="unable to add physical address to employee", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details: EmployeeDetails = await company_controller.get_employee_by_uid(uid=user.uid)
    if not isinstance(employee_details, EmployeeDetails):
        flash(message="Employee details not found please try again later", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    address: Address = await company_controller.add_update_address(address=physical_address)
    if not isinstance(address, Address):
        flash(message="could not add/update physical address", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details.address_id = address.address_id
    employee = await employee_controller.add_update_employee_details(employee_details=employee_details)

    if not isinstance(employee, EmployeeDetails):
        flash(message="unable to add/update physical address to employee", category="danger")

    flash(message="successfully updated employee details", category="success")
    return redirect(url_for('employees.get_employee_details'))


@employee_route.post('/admin/employee-details/update-banking')
@login_required
async def update_banking_details(user: User):
    """
        **update_banking_details**
    :param user:
    :return:
    """
    try:
        bank_account: BankAccount = BankAccount(**request.form)
    except ValidationError as e:
        employee_logger.error(str(e))
        flash(message="unable to add physical address to employee", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details: EmployeeDetails = await company_controller.get_employee_by_uid(uid=user.uid)
    if not isinstance(employee_details, EmployeeDetails):
        flash(message="Employee details not found please try again later", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    account: BankAccount = await company_controller.add_bank_account(bank_account=bank_account)
    if not isinstance(account, BankAccount):
        flash(message="could not add/update bank account", category="danger")
        return redirect(url_for('employees.get_employee_details'))

    employee_details.bank_account_id = account.bank_account_id
    employee = await employee_controller.add_update_employee_details(employee_details=employee_details)

    if not isinstance(employee, EmployeeDetails):
        flash(message="unable to add/update bank account to employee record", category="danger")

    flash(message="successfully updated employee details", category="success")
    return redirect(url_for('employees.get_employee_details'))


@employee_route.get('/admin/administrators/employees')
@login_required
async def get_employees(user: User):
    """
        **get_employees**

        :param user:
        :return:
    """
    company_branches: CompanyBranches = await company_controller.get_company_branches(company_id=user.company_id)
    employees_list: list[EmployeeDetails] = await company_controller.get_company_employees(company_id=user.company_id)
    context = dict(user=user, employees_list=employees_list, branches=company_branches)
    return render_template("admin/managers/employees.html", **context)


# noinspection DuplicatedCode
@employee_route.get('/admin/administrators/employee/<string:employee_id>')
@login_required
async def get_employee_detail(user: User, employee_id: str):
    """
        **get_employee_detail**
        :param user:
        :param employee_id:
        :return:
    """
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_employee_id(
        employee_id=employee_id)
    employee_logger.info(f"Employee Detail : {employee_detail}")
    if not employee_detail:
        flash(message="catastrophic failure", category="danger")
        return redirect(url_for('employees.get_employees'))

    salary_detail: Salary = await employee_controller.get_salary_details(employee_id=employee_detail.employee_id)
    context = dict(user=user, employee_detail=employee_detail, salary_detail=salary_detail)
    context = await add_data_employee(context, employee_detail)

    return render_template('admin/managers/employees/view.html', **context)


@employee_route.get('/admin/employees/attendance-register')
@login_required
async def get_attendance_register(user: User):
    """
    **get_attendance_register**
    :param user:
    :return:
    """
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)
    context: dict[str, User | EmployeeDetails] = dict(user=user, employee_detail=employee_detail)

    return render_template('hr/attendance-register.html', **context)


# noinspection DuplicatedCode
@employee_route.post('/admin/employees/attendance-register/clock-in')
@login_required
async def employee_clocking_in(user: User):
    """
    **employee_clocking_in**
    :param user:
    :return:
    """
    employee_id: str = request.form.get('employee_id')
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)
    employee_logger.info(f"IS Company ADMIN : {user.is_company_admin}")

    if not employee_detail and not (employee_detail.is_active and user.can_access_employee_record):
        message: str = "Either your account is De Activated or you have not verified your User Account"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    # The Fact that Company Admin could proceed and Sign In Maybe Bad Logic
    if employee_id != employee_detail.employee_id and not user.is_company_admin:
        message: str = "You are Not Authorized to Clock in for this Employee"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    has_signed_in: bool = await employee_controller.sign_in_employee(employee_detail=employee_detail)

    if has_signed_in:
        sign_in_time = datetime.datetime.now().strftime("%I:%M %p")
        flash(message=f"Successfully signed in at: {sign_in_time}", category="success")
    else:
        flash(message="Error signing in. Or Employee Already Signed IN.", category="danger")

    return redirect(url_for('employees.get_attendance_register'))


# noinspection DuplicatedCode
@employee_route.post('/admin/employees/attendance-register/clock-out')
@login_required
async def employee_clocking_out(user: User):
    """

    :param user:
    :return:
    """
    employee_id: str = request.form.get('employee_id')
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)

    if not employee_detail and not (employee_detail.is_active and (user.is_employee or user.is_company_admin)):
        message: str = "you have no proper employee record please inform admin"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    if employee_id != employee_detail.employee_id:
        message: str = "You are Not Authorized to Clock in for this Employee"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    has_signed_out: bool = await employee_controller.sign_out_employee(employee_detail=employee_detail)

    if has_signed_out:
        sign_out_time = datetime.datetime.now().strftime("%I:%M %p")
        flash(message=f"Successfully signed out at: {sign_out_time}", category="success")
    else:
        flash(message="Error signing out. try again later.", category="danger")

    return redirect(url_for('employees.get_attendance_register'))


@employee_route.post('/admin/employees/update-salary')
@login_required
async def update_salary_record(user: User):
    """

    :param user:
    :return:
    """
    try:
        salary: Salary = Salary(**request.form)
        employee_logger.info(f"Salary : {salary}")
    except ValidationError as e:
        employee_id = request.form.get('employee_id')
        if employee_id:
            return redirect(url_for('employees.get_employee_detail', employee_id=employee_id))
        return redirect(url_for('employees.get_employees'))

    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_employee_id(
        employee_id=salary.employee_id)

    # TODO may need to remove this but this ensures that the salary record is equivalent to the employee record
    employee_detail.salary = salary.amount
    employee_detail = await employee_controller.add_update_employee_details(employee_details=employee_detail)

    if not isinstance(employee_detail, EmployeeDetails):
        mess: str = "unable to update employee salary details - employee not found please try again later"
        flash(message=mess, category='danger')
        return redirect(url_for('employees.get_employees'))

    updated_salary: Salary = await employee_controller.add_update_employee_salary(salary=salary)
    if not isinstance(updated_salary, Salary):
        flash(message="Unable to Update Employee Salary please try again later", category='danger')
        return redirect(url_for('employees.get_employee_detail', employee_id=salary.employee_id))

    employee_logger.info(f"Updated Salary : {updated_salary}")
    flash(message="successfully updated employee salary record", category='success')
    return redirect(url_for('employees.get_employee_detail', employee_id=salary.employee_id))


@employee_route.get('/admin/employees/work-summary')
@login_required
async def get_work_summary(user: User):
    """
    :param user:
    :return:
    """
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)
    employee_logger.info(f'Complete Employee Records : {employee_detail}')
    context = dict(user=user, employee_detail=employee_detail)
    return render_template('hr/work-summary.html', **context)


@employee_route.get('/admin/employees/payslips')
@login_required
async def get_payslips(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('hr/payslips.html', **context)


@employee_route.get('/admin/employees/payroll')
@login_required
async def get_payroll(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('hr/payroll.html', **context)
