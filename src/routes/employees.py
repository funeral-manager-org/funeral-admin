import datetime
from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError
from twilio.twiml.voice_response import Pay

from src.database.models.bank_accounts import BankAccount
from src.authentication import login_required, admin_login
from src.database.models.companies import EmployeeDetails, CompanyBranches, Salary, WorkSummary, Payslip, Company, \
    AttendanceSummary
from src.database.models.contacts import Contacts, PostalAddress, Address
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, employee_controller

employee_route = Blueprint('employees', __name__)
employee_logger = init_logger('employee_route')

# Type Vars for Payslip Compilation adn Formatting
HistorocalPaySlipType = dict[str, list[tuple[EmployeeDetails, Payslip]]]
LatestPaySlipType = list[tuple[EmployeeDetails, Payslip]]


# route utils
async def retrieve_create_this_month_payslip(employee_id: str, salary: Salary) -> Payslip | None:

    # creating a new payslip for the current pay period
    payslip: Payslip | None = await employee_controller.get_present_employee_payslip(employee_id=employee_id)
    if not payslip:
        try:
            payslip = Payslip(employee_id=employee_id, salary_id=salary.salary_id)
        except ValidationError as e:
            employee_logger.warning(str(e))
            return None

        payslip = await employee_controller.create_employee_payslip(payslip=payslip)

    employee_logger.info(f"Employee Payslip Found: {payslip}")
    return payslip


async def create_retrieve_salary(employee_detail: EmployeeDetails):
    """
        **create_salary**
             create salary model and save to database
    :param employee_detail:
    :return:
    """
    employee_id = employee_detail.employee_id
    salary: Salary = await employee_controller.get_salary_details(employee_id=employee_id)
    if not salary:
        new_salary: Salary = Salary(employee_id=employee_detail.employee_id, company_id=employee_detail.company_id,
                           branch_id=employee_detail.branch_id, amount=employee_detail.salary, pay_day=1)

        salary: Salary = await employee_controller.add_update_employee_salary(salary=new_salary)

    employee_logger.info(f"Successfully Created or Retrieved Employee Salary Record : {salary}")

    return salary

async def retrieve_create_attendance_register(employee_detail: EmployeeDetails) -> AttendanceSummary | None:
    employee_id: str = employee_detail.employee_id
    attendance_register = await employee_controller.get_employee_attendance_register(employee_id=employee_id)
    if not attendance_register:
        employee_logger.info(f"Started Creating Attendance Register")

        try:
            new_register = AttendanceSummary(employee_id=employee_id, name=employee_detail.display_names)
            employee_logger.info(f"New Attendance Register: {new_register}")
            attendance_register = await employee_controller.add_update_attendance_register(attendance_register=new_register)

        except ValidationError as e:
            employee_logger.warning(str(e))
            return None

    return attendance_register


async def retrieve_create_work_summary(attendance_id: str, payslip_id: str, employee_id: str):
    """"""

    try:
        work_summary = await employee_controller.get_employee_current_work_summary(employee_id=employee_id)
        if not work_summary:
            # creating current pay period work summary
            current_work_summary = WorkSummary(attendance_id=attendance_id, payslip_id=payslip_id, employee_id=employee_id)

            work_summary = await employee_controller.add_update_current_work_summary(work_summary=current_work_summary)
        if not work_summary:
            employee_logger.error("Unable to create Employee Work Summary")
            return None
    except ValidationError as e:
        employee_logger.warning(str(e))
        return None

    return work_summary


async def create_work_documents(employee_detail: EmployeeDetails):
    """this creates payslips and Work Summary for the Current Month for the Employee"""
    employee_id: str = employee_detail.employee_id
    salary = await create_retrieve_salary(employee_detail=employee_detail)

    employee_logger.info(f"Salary Details Found : {salary}")


    attendance_register = await retrieve_create_attendance_register(employee_detail=employee_detail)

    if not attendance_register:
        employee_logger.error("Unable to create or retrieve Attendance Register")
        return False

    employee_logger.info(f"Employee Attendance Register Found: {attendance_register}")
    payslip = await retrieve_create_this_month_payslip(employee_id=employee_id, salary=salary)
    if not payslip:
        employee_logger.error("Unable to obtain or create the latest payslip")
    attendance_id = attendance_register.attendance_id
    payslip_id = payslip.payslip_id
    work_summary = await retrieve_create_work_summary(attendance_id=attendance_id, payslip_id=payslip_id,
                                                      employee_id=employee_id)

    return work_summary


# Routes

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

        employee_id = employee_detail.employee_id
        current_work_summary = await employee_controller.get_employee_current_work_summary(employee_id=employee_id)

        if not isinstance(current_work_summary, WorkSummary):
            # without current month work summary lets create a default one the manager can still edit the work summary
            work_documents_created = await create_work_documents(employee_detail=employee_detail)
            if not work_documents_created:
                employee_signed_out = await employee_controller.sign_out_employee(employee_detail=employee_detail)
                employee_logger.error("Unable to sign in Employee - we have signed out the Employee")
                flash(message="Employee Could not Sign In Due to Errors creating work documents please inform admin", category="danger")
            else:
                flash(message="Employee Signed In Please Remember to sign off Employee when Off Duty")
    else:
        flash(message="Error signing in. Or Employee Already Signed IN.", category="danger")

    return redirect(url_for('employees.get_attendance_register'))



# noinspection DuplicatedCode
@employee_route.post('/admin/employees/attendance-register/clock-out')
@login_required
async def employee_clocking_out(user: User):
    """
        **employee_clocking_out**
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
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_uid(uid=user.uid)

    context = dict(user=user, employee_detail=employee_detail)
    return render_template('hr/payslips.html', **context)


async def get_historical_payslips(employee_list: list[EmployeeDetails]) -> HistorocalPaySlipType:
    """
    Retrieves historical payslips for a user, organized by year and month.

    :param user: The user requesting historical payslips.
    :return: A dictionary with keys formatted as "YYYY-month" and values as lists of (EmployeeDetails, Payslip) tuples.
    """

    # Initialize the dictionary with default list
    payslips_by_month: dict[str, list[tuple[EmployeeDetails, Payslip]]] = defaultdict(list)

    for employee in employee_list:
        for payslip in employee.payslip:
            # Format the key as "YYYY-month"
            key = payslip.pay_period_start.strftime("%Y-%B").title()
            payslips_by_month[key].append((employee, payslip))

    return payslips_by_month

async def get_latest_payslips(employee_list) -> LatestPaySlipType:
    async def latest_payslip(payslips: list[Payslip]) -> Payslip:
        """
        Finds the latest payslip from a list of payslips based on the pay period end date.

        :param payslips: List of payslips to check.
        :return: The latest payslip.
        """
        if not payslips:
            return None  # Handle case with no payslips

        # Sort payslips by pay_period_end and return the last one
        sorted_payslips = sorted(payslips, key=lambda x: x.pay_period_end)
        return sorted_payslips[-1]

    return [(employee, await latest_payslip(payslips=employee.payslip))
            for employee in employee_list if employee.payslip]

@employee_route.get('/admin/employees/payroll')
@admin_login
async def get_payroll(user: User):
    """
    Retrieves the payroll information for a given user.

    :param user: The user requesting payroll information.
    :return: Redirects to the admin page if the user is not registered, otherwise provides payroll details.
    """
    if user and not user.company_id:
        message: str = "Not registered on any company"
        flash(message=message, category='danger')
        return redirect(url_for('company.get_admin'))

    employee_list: list[EmployeeDetails] = await employee_controller.get_complete_employee_details_for_company(
        company_id=user.company_id)

    latest_payslips: list[tuple[EmployeeDetails, Payslip]] = await get_latest_payslips(employee_list=employee_list)
    historical_payslips:HistorocalPaySlipType = await get_historical_payslips(employee_list=employee_list)
    # Do something with latest_employee_payslip
    # For example, you could render a template with this information:
    # return render_template('payroll.html', latest_employee_payslip=latest_employee_payslip)
    # employee_logger.info(latest_payslips)
    # employee_logger.info("++++++++++++++++++++++++++++++++++++++++")
    # employee_logger.info(historical_payslips)
    context = dict(user=user, latest_payslips=latest_payslips, historical_payslips=historical_payslips)
    return render_template('hr/payroll.html', **context)




@employee_route.get('/admin/employees/work-docs/<string:employee_id>')
@admin_login
async def create_work_docs(user: User, employee_id: str):
    """

    :param user:
    :param employee_id:
    :return:
    """
    employee_detail: EmployeeDetails = await employee_controller.get_employee_complete_details_employee_id(employee_id=employee_id)

    if not isinstance(employee_detail, EmployeeDetails):
        message: str = "This is not a Valid Employee"
        flash(message=message, category="danger")
        return redirect(url_for("employees.get_employees"))

    # checking if employee lacks any of the needed documents if yes then create them
    if not all(getattr(employee_detail, attr) for attr in ['attendance_register', 'work_summary', 'payslip']):
        employee_logger.info("Started Creating Work Documents for Employee")
        if await create_work_documents(employee_detail=employee_detail):
            message: str = "Successfully created work documents"
            flash(message=message,category="success")
        else:
            message: str = "Unable to create work documents"
            flash(message=message, category="danger")



    return redirect(url_for('employees.get_employee_detail', employee_id=employee_id))
