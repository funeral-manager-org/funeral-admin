import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.logger import init_logger
from src.authentication import login_required, admin_login
from src.database.models.companies import EmployeeDetails, AttendanceSummary
from src.database.models.users import User
from src.main import company_controller, employee_controller

employee_route = Blueprint('employees', __name__)
employee_logger = init_logger('employee_route')


async def add_data_employee(context, employee_detail):
    if not employee_detail:
        return

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


@employee_route.get('/admin/employee-details')
@login_required
async def get_employee_details(user: User):
    """

    :param user:
    :return:
    """
    employee_logger.info(user)
    if not user.can_access_employee_record:
        message: str = "you have no proper employee record please inform admin"
        flash(message=message, category="danger")
        return redirect(url_for('home.get_home'))
    context = dict(user=user)
    employee_detail: EmployeeDetails | None = None
    employee_detail = await employee_controller.get_employee_complete_details_uid(
        uid=user.uid)

    if employee_detail:
        # this adds postal addresses and others
        await add_data_employee(context=context, employee_detail=employee_detail)
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
    pass


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
    context = dict(user=user, employee_detail=employee_detail)
    await add_data_employee(context, employee_detail)

    return render_template('admin/managers/employees/view.html', **context)


@employee_route.get('/admin/employees/attendance-register')
@login_required
async def get_attendance_register(user: User):
    """

    :param user:
    :return:
    """
    # records = get_records()
    # # Check if the user has clocked in
    # clocked_in = any(record.clock_in for record in records)
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)
    context = dict(user=user, employee_detail=employee_detail)
    employee_logger.info(context)
    return render_template('hr/attendance-register.html', **context)


@employee_route.post('/admin/employees/attendance-register/clock-in')
@login_required
async def employee_clocking_in(user: User):
    """

    :param user:
    :return:
    """
    employee_id: str = request.form.get('employee_id')
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)

    if not (employee_detail and employee_detail.is_active and user.is_employee):
        message: str = "you have no proper employee record please inform admin"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    if employee_id != employee_detail.employee_id:
        message: str = "error clocking in"
        flash(message=message, category="danger")
        return redirect(url_for('employees.get_attendance_register'))

    has_signed_in = await employee_controller.sign_in_employee(employee_detail=employee_detail)

    if has_signed_in:
        sign_in_time = datetime.datetime.now().strftime("%I:%M %p")
        flash(message=f"Successfully signed in at: {sign_in_time}", category="success")
    else:
        flash(message="Error signing in. Please try again later.", category="danger")

    return redirect(url_for('employees.get_attendance_register'))


@employee_route.post('/admin/employees/attendance-register/clock-out')
@login_required
async def employee_clocking_out(user: User):
    """

    :param user:
    :return:
    """
    pass


@employee_route.get('/admin/employees/work-summary')
@login_required
async def get_work_summary(user: User):
    """
    :param user:
    :return:
    """
    context = dict(user=user)
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
