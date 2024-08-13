from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.logger import init_logger
from src.database.models.bank_accounts import BankAccount
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.authentication import login_required, admin_login
from src.database.models.companies import Company, CompanyBranches, EmployeeDetails, Salary
from src.database.models.users import User
from src.main import company_controller, user_controller, encryptor, employee_controller
from src.utils import create_id

company_route = Blueprint('company', __name__)
error_logger = init_logger('company_logger')


@company_route.get('/admin')
@login_required
async def get_admin(user: User):
    """

    :return:
    """
    context = dict(user=user)

    if user.company_id:
        company_data: Company = await company_controller.get_company_details(company_id=user.company_id)
        company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    else:
        company_data = {}
        company_branches = []
    context.update(company=company_data, company_branches=company_branches)

    if user.is_system_admin:
        return render_template('admin/managers/manager.html', **context)
    elif user.is_company_admin:
        return render_template('admin/managers/manager.html', **context)
    elif user.can_access_employee_record:
        return render_template('admin/employees/employee.html', **context)
    elif user.is_client:
        return render_template('admin/clients/clients.html', **context)

    message = """If you want to register your funeral company please click on register company below
    If you are an employee of a funeral company that uses this system please inform your administrator so they can register you
    on their company"""

    flash(message=message, category='success')

    return render_template('admin/managers/manager.html', **context)


@company_route.get('/admin/company/company-administrator')
@login_required
async def get_company_administrator(user: User):
    """

    :param user:
    :return:
    """
    _user: User = await user_controller.get_account_by_uid(uid=user.uid)
    if not _user.company_id:
        flash(message="You are not registered in any company", category="danger")
        return redirect(url_for('company.get_admin'))

    admin_details: EmployeeDetails = await company_controller.get_company_administrator(company_id=user.company_id)
    error_logger.info(f"Company Admin : {admin_details}")
    error_logger.info(f"user Info : {_user}")
    company_branches = await company_controller.get_company_branches(company_id=_user.company_id)
    employee_roles = await company_controller.get_employee_roles(company_id=_user.company_id)
    context = dict(
        user=user,
        admin_details=admin_details,
        employee_roles=employee_roles,
        company_branches=company_branches
    )
    return render_template('admin/tasks/company/register_me.html', **context)


@company_route.post('/admin/company/update-company-administrator')
@admin_login
async def update_company_administrator(user: User):
    """

    :param user:
    :return:
    """
    try:
        if not request.form.get('uid'):
            admin_employee_detail: EmployeeDetails = EmployeeDetails(**request.form,
                                                                     uid=user.uid, company_id=user.company_id)
        else:
            admin_employee_detail: EmployeeDetails = EmployeeDetails(**request.form)

    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Unable to update Administrator Detail please see log files", category="danger")
        return redirect(url_for('company.get_admin'))

    # This is because user may not have the same branch id as in employee record
    if admin_employee_detail.branch_id and not user.branch_id:
        user.branch_id = admin_employee_detail.branch_id
        _ = await user_controller.put(user=user)

    admin_added, _ = await company_controller.add_update_employee(employee=admin_employee_detail)
    if not admin_added:
        flash(message="Error Adding new company Administrator", category="danger")
        return redirect(url_for('company.get_admin'))

    old_salary: Salary = await employee_controller.get_salary_details(employee_id=admin_employee_detail.employee_id)
    if not old_salary:
        #
        new_salary = Salary(employee_id=admin_employee_detail.employee_id, company_id=admin_employee_detail.company_id,
                            branch_id=admin_employee_detail.branch_id,
                            amount=admin_employee_detail.salary,
                            pay_day=1)

        _ = await employee_controller.add_update_employee_salary(salary=new_salary)
    else:
        # should update salary record if old salary amount is not the same as new salary amount
        if old_salary.amount != admin_employee_detail.salary:
            old_salary.amount = admin_employee_detail.salary
            _ = await employee_controller.add_update_employee_salary(salary=old_salary)

    flash(message="Successfully updated company administrator details", category="success")
    return redirect(url_for('company.get_admin'))


@company_route.get('/admin/company/register')
@login_required
async def get_register(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    if user.company_id:
        company_details = await company_controller.get_company_details(company_id=user.company_id)
        context.update(company_details=company_details)
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

    registered_company = await company_controller.register_company(company=company)
    if not registered_company:
        flash(message="Unable to Register Company please try again later", category="danger")
        return redirect(url_for('company.get_register'))

    user.is_company_admin = True
    user.company_id = registered_company.company_id
    # Updating User as Admin of the New Company
    updated_user = await user_controller.put(user=user)

    if not updated_user:
        # will remove the company as there was an error updating the new user to own the company
        flash(message="Company Registered with Errors please contact admin", category="danger")
        is_deleted = await company_controller.delete_company_details(company_id=registered_company.company_id)

    flash(message="company successfully registered", category="success")
    # context = dict(user=updated_user, company_data=registered_company)
    return redirect(url_for('company.get_admin'))


@company_route.post('/admin/company/update')
@admin_login
async def update_company_details(user: User):
    """

    :param user:
    :return:
    """
    try:
        company_details = Company(**request.form)
    except ValidationError as e:
        error_logger.warning(str(e))
        flash(message="Unable to Update Company as some values are not filled in", category='danger')
        return redirect(url_for('company.get_register'))

    if user.uid != company_details.admin_uid:
        flash(message="You are not authorized to update this company details please inform admin", category="danger")
        return redirect(url_for('company.get_admin'))

    updated_company = await company_controller.update_company_details(company_details=company_details)
    if not updated_company:
        flash(message="Unable to update company please try again later", category="danger")
        return redirect(url_for('company.get_register'))

    flash(message="Company Successfully updated", category="success")
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

    flash(message="branch successfully added", category="success")
    return redirect(url_for('company.get_admin'))


@company_route.post('/admin/company/edit-branch')
@admin_login
async def update_company_branch(user: User):
    """

    :param user:
    :return:
    """
    try:
        branch_detail = CompanyBranches(**request.form)
        if branch_detail.company_id != user.company_id:
            flash(message="You are not authorized to update this branch details")
    except ValidationError as e:
        error_logger.warning(str(e))
        flash(message="cannot update branch details please complete the details", category='danger')
        return redirect(url_for('company.get_admin'))

    branch_company_details: Company = await company_controller.get_company_details(company_id=branch_detail.company_id)
    if branch_company_details.admin_uid != user.uid:
        flash(message="You Are not Authorized to Update this company branch details please contact admin",
              category="danger")
        return redirect(url_for('company.get_admin'))

    updated_branch = await company_controller.update_company_branch(company_branch=branch_detail)
    if not updated_branch:
        flash(message="Error updating Branch - please try again later", category="danger")
        return redirect(url_for('company.get_admin'))

    flash(message="branch successfully updated", category="success")
    return redirect(url_for('company.get_admin'))


@company_route.get('/admin/company/branch/<string:branch_id>')
@login_required
async def get_branch(user: User, branch_id: str):
    """

    :param user:
    :param branch_id:
    :return:
    """
    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    if not branch:
        flash(message="Error fetching branch", category="danger")
        return redirect(url_for('company.get_admin'))
    employee_roles: list[str] = await company_controller.get_employee_roles(company_id=user.company_id)
    employee_list: list[EmployeeDetails] = await company_controller.get_branch_employees(branch_id=branch_id)

    error_logger.info(f"Employee List : {employee_list}")

    context = dict(user=user, branch=branch, employee_roles=employee_roles, employee_list=employee_list,
                   total_employees=len(employee_list))

    if branch.address_id:
        address = await company_controller.get_address(address_id=branch.address_id)
        context.update(address=address)

    if branch.postal_id:
        postal = await company_controller.get_postal_address(postal_id=branch.postal_id)
        context.update(postal_address=postal)

    if branch.contact_id:
        contact = await company_controller.get_contact(contact_id=branch.contact_id)
        context.update(contact=contact)

    if branch.bank_account_id:
        bank_account = await company_controller.get_bank_account(bank_account_id=branch.bank_account_id)
        context.update(bank_account=bank_account)

    return render_template('admin/managers/branches/details.html', **context)


@company_route.post('/admin/company/branch/add-branch-address/<string:branch_id>')
@login_required
async def add_branch_address(user: User, branch_id: str):
    """
        this will add or update a branch address
    :param branch_id:
    :param user:
    :return:
    """
    try:
        branch_address: Address = Address(**request.form)
    except ValidationError as e:
        flash(message="Error adding branch address please input all fields", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    branch_address_ = await company_controller.add_update_address(address=branch_address)
    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.address_id = branch_address_.address_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)
    if not updated_branch:
        flash(message="Error Adding company branch physical address", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    flash(message="successfully updated branch physical address", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/branch-postal-address/<string:branch_id>')
@login_required
async def add_postal_address(user: User, branch_id: str):
    """

    :param user:
    :param branch_id:
    :return:
    """
    try:
        branch_postal_address = PostalAddress(**request.form)
    except ValidationError as e:
        flash(message="Error adding branch address please input all fields", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    branch_postal_address_ = await company_controller.add_postal_address(postal_address=branch_postal_address)

    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.postal_id = branch_postal_address_.postal_id
    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    if not updated_branch:
        flash(message="Error Adding Company Branch Postal Address", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    flash(message="successfully updated branch postal address", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/branch-contact/<string:branch_id>')
@login_required
async def add_update_branch_contacts(user: User, branch_id: str):
    """

    :param user:
    :param branch_id:
    :return:
    """
    try:

        branch_contacts = Contacts(**request.form)
    except ValidationError as e:
        flash(message="Please ensure to fill in all required fields", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    branch_contacts_ = await company_controller.add_contacts(contact=branch_contacts)
    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.contact_id = branch_contacts_.contact_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    if not updated_branch:
        flash(message="Error Adding Company Branch Contact Details", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    flash(message="successfully updated branch contact details", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/bank-account/add/<string:branch_id>')
@login_required
async def add_bank_account(user: User, branch_id: str):
    """

    :param user:
    :param branch_id:
    :return:
    """
    try:
        branch_bank_account = BankAccount(**request.form)
    except ValidationError as e:
        flash(message="Please fill in all required fields", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    branch_bank_account_ = await company_controller.add_bank_account(bank_account=branch_bank_account)

    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.bank_account_id = branch_bank_account_.bank_account_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    flash(message="successfully updated branch bank account", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/employee/add/<string:branch_id>')
@login_required
async def add_employee(user: User, branch_id: str):
    """

    :param branch_id:
    :param user:
    :return:
    """
    try:
        new_employee = EmployeeDetails(**request.form)

        # Employee is added to the company of the Company Admin and to the branch presently opened
        new_employee.company_id = user.company_id
        new_employee.branch_id = branch_id
        new_employee.email = new_employee.email.lower().strip()

    except ValidationError as e:
        error_logger.warning(str(e))
        flash(message="Please fill in all required employee details", category='danger')
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    new_employee, employee_ = await company_controller.add_update_employee(employee=new_employee)
    if new_employee:
        branch = await company_controller.get_branch_by_id(branch_id=branch_id)
        branch.total_employees += 1
        _ = await company_controller.update_company_branch(company_branch=branch)

        if employee_.email:

            new_user = await user_controller.get_by_email(email=employee_.email)

            if new_user:
                pass
            else:

                await create_new_employee_user_detail(branch_id=branch_id, employee_=employee_, user=user)

            message = """
            Your Employee has successfully been added.
                We have sent an Email to your employee with their login details
                Your Employee also need to click a link on the email to verify their email address            
            """
            flash(message=message, category="success")
            return redirect(url_for('company.get_branch', branch_id=branch_id))

    if employee_:
        message = "Employee was successfully updated"
        flash(message=message, category="success")
    else:
        message = "We where unable to add your employee please try again if the problem persists please notify admin"
        flash(message=message, category="danger")

    return redirect(url_for('company.get_branch', branch_id=branch_id))


async def create_new_employee_user_detail(branch_id: str, employee_: EmployeeDetails, user: User):
    """
        when adding a new employee use this to create a new user record for the employee
        and then send a verification email
    :param branch_id:
    :param employee_:
    :param user:
    :return:
    """
    password = await user_controller.create_employee_password()
    password_hash = encryptor.create_hash(password=password)

    _new_user = User(uid=create_id(),
                     branch_id=branch_id,
                     company_id=user.company_id,
                     username=employee_.email,
                     email=employee_.email,
                     password_hash=password_hash,
                     is_employee=True)

    new_employee_user = await user_controller.update_employee_user_record(user=_new_user)
    # Updating UID for Employee
    employee_.uid = _new_user.uid
    # Add or Update Employee Record
    employee_updated, _ = await company_controller.add_update_employee(employee=employee_)

    # Create New Salary Record - default of the 1st as payday
    new_salary = Salary(employee_id=employee_.employee_id, company_id=employee_.company_id,
                        branch_id=employee_.branch_id, amount=employee_.salary, pay_day=1)

    _ = await employee_controller.add_update_employee_salary(salary=new_salary)

    # Sending Verification Email for New Employees
    _ = await user_controller.send_verification_email(user=new_employee_user,
                                                      password=password)


# noinspection DuplicatedCode
@company_route.get('/admin/company/branch/employee/get/<string:branch_id>/<string:employee_id>')
@login_required
async def get_employee(user: User, branch_id: str, employee_id: str):
    """

    :param user:
    :param employee_id:
    :param branch_id:
    :return:
    """
    employee_detail: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)
    employee_roles: list[str] = await company_controller.get_employee_roles(company_id=user.company_id)

    if employee_detail:
        branch = await company_controller.get_branch_by_id(branch_id=branch_id)
        context = dict(user=user, employee_detail=employee_detail, branch=branch, employee_roles=employee_roles)

        if employee_detail.uid:
            user_employee: User = await user_controller.get_account_by_uid(uid=employee_detail.uid)
            context.update(user_employee=user_employee)

        if employee_detail.address_id:
            address = await company_controller.get_address(address_id=employee_detail.address_id)
            context.update(address=address)

        if employee_detail.postal_id:
            postal_address = await company_controller.get_postal_address(postal_id=employee_detail.postal_id)
            context.update(postal_address=postal_address)

        if employee_detail.bank_account_id:
            bank_account = await company_controller.get_bank_account(bank_account_id=employee_detail.bank_account_id)
            context.update(bank_account=bank_account)

        if employee_detail.contact_id:
            contact = await company_controller.get_contact(contact_id=employee_detail.contact_id)
            context.update(contact=contact)
        print(context)
        return render_template('admin/managers/branches/employee.html', **context)


@company_route.post('/admin/company/branch/employee/address/add/<string:branch_id>/<string:employee_id>')
@login_required
async def add_employee_address(user: User, branch_id: str, employee_id: str):
    """

    :return:
    """
    try:
        address = Address(**request.form)
    except ValidationError as e:
        flash(message="Please input all required fields", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    employee: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)
    if employee.company_id != user.company_id:
        flash(message="You are not authorized to perform this action please contact admin", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    address = await company_controller.add_update_address(address=address)
    if not address:
        message = "Error updating employee physical address"
        flash(message=message, category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    # Updating Address ID
    employee.address_id = address.address_id

    is_updated, _ = await company_controller.add_update_employee(employee=employee)
    if not is_updated:
        flash(message="Error Adding New Employee Address please try again later", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    message = "successfully update employee physical address"
    flash(message=message, category="success")
    return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))


@company_route.post('/admin/company/branch/employee/bank-account/add/<string:branch_id>/<string:employee_id>')
@login_required
async def add_employee_bank_account(user: User, branch_id: str, employee_id: str):
    """

    :param branch_id:
    :param user:
    :param employee_id:
    :return:
    """
    try:
        bank_account = BankAccount(**request.form)
    except ValidationError as e:
        error_logger.warning(str(e))
        flash(message="Please input all required fields", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    employee: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)
    if employee.company_id != user.company_id:
        flash(message="You are not authorized to perform this action please contact admin", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    bank_account = await company_controller.add_bank_account(bank_account=bank_account)
    if not bank_account:
        message = "Unable to create or update bank account"
        flash(message=message, category="success")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    # Updating Bank account ID on Employee Record
    employee.bank_account_id = bank_account.bank_account_id
    is_updated, _ = await company_controller.add_update_employee(employee=employee)

    if not is_updated:
        flash(message="Error Adding New Employee Bank Details please try again later", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    message = "successfully update employee bank account"
    flash(message=message, category="success")
    return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))


# noinspection DuplicatedCode
@company_route.post('/admin/company/branch/employee/contacts/add/<string:branch_id>/<string:employee_id>')
@login_required
async def add_employee_contacts(user: User, branch_id: str, employee_id: str):
    """

    :param user:
    :param branch_id:
    :param employee_id:
    :return:
    """
    try:
        contact = Contacts(**request.form)
    except ValidationError as e:
        flash(message="Please input all required fields", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    employee: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)
    if employee.company_id != user.company_id:
        flash(message="You are not authorized to perform this action please contact admin", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    contact = await company_controller.add_contacts(contact=contact)

    # Updating Employee Contact Details to point to the correct Contact Details Record
    employee.contact_id = contact.contact_id
    is_updated, _ = await company_controller.add_update_employee(employee=employee)

    if not is_updated:
        flash(message="Error Adding New Employee Contact Details please try again later", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    message = "successfully update employee contact details"
    flash(message=message, category="success")
    return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))


@company_route.post('/admin/company/branch/employee/postal-address/add/<string:branch_id>/<string:employee_id>')
@login_required
async def add_employee_postal_address(user: User, branch_id: str, employee_id: str):
    """

    :param user:
    :param branch_id:
    :param employee_id:
    :return:
    """
    try:
        postal_address = PostalAddress(**request.form)
    except ValidationError as e:
        flash(message="Please input all required fields", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    employee: EmployeeDetails = await company_controller.get_employee(employee_id=employee_id)
    if employee.company_id != user.company_id:
        flash(message="You are not authorized to perform this action please contact admin", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    # Updating Employee Postal ID
    postal_address = await company_controller.add_postal_address(postal_address=postal_address)

    employee.postal_id = postal_address.postal_id

    is_updated, _ = await company_controller.add_update_employee(employee=employee)
    if not is_updated:
        flash(message="Error Adding New Employee Postal Address please try again later", category="danger")
        return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))

    message = "successfully update employee contact details"
    flash(message=message, category="success")
    return redirect(url_for('company.get_employee', branch_id=branch_id, employee_id=employee_id))
