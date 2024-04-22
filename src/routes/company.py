from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.models.bank_accounts import BankAccount
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.authentication import login_required
from src.database.models.companies import Company, CompanyBranches, EmployeeDetails
from src.database.models.users import User
from src.main import company_controller, user_controller, encryptor
from src.utils import create_id

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
        print(f"branches : {company_branches}")
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

    flash(message="branch successfully added", category="success")
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
    print("#################################################")
    print(employee_list)
    context = dict(user=user, branch=branch, employee_roles=employee_roles, employee_list=employee_list)

    if branch.address_id:
        address = await company_controller.get_branch_address(address_id=branch.address_id)
        context.update(address=address)

    if branch.postal_id:
        postal = await company_controller.get_branch_postal_address(postal_id=branch.postal_id)
        context.update(postal_address=postal)

    if branch.contact_id:
        contact = await company_controller.get_branch_contact(contact_id=branch.contact_id)
        context.update(contact=contact)

    if branch.bank_account_id:
        bank_account = await  company_controller.get_branch_bank_account(bank_account_id=branch.bank_account_id)
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
        branch_address = Address(**request.form)
    except ValidationError as e:
        flash(message="Error adding branch address please input all fields", category="danger")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    branch_address_ = await company_controller.add_update_branch_address(branch_address=branch_address)
    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.address_id = branch_address_.address_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)
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

    branch_postal_address_ = await company_controller.add_branch_postal_address(
        branch_postal_address=branch_postal_address)

    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.postal_id = branch_postal_address_.postal_id
    updated_branch = await company_controller.update_company_branch(company_branch=branch)
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

    branch_contacts_ = await company_controller.add_branch_contacts(branch_contacts=branch_contacts)
    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.contact_id = branch_contacts_.contact_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    flash(message="successfully updated branch contact details", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/bank-account/<string:branch_id>')
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

    branch_bank_account_ = await company_controller.add_branch_bank_account(branch_bank_account=branch_bank_account)

    branch: CompanyBranches = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.bank_account_id = branch_bank_account_.bank_account_id

    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    flash(message="successfully updated branch bank account", category="success")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


@company_route.post('/admin/company/branch/add-employee/<string:branch_id>')
@login_required
async def add_employee(user: User, branch_id: str):
    """

    :param branch_id:
    :param user:
    :return:
    """
    try:
        new_employee = EmployeeDetails(**request.form)

        new_employee.company_id = user.company_id
        new_employee.branch_id = branch_id
        new_employee.email = new_employee.email.lower().strip()
    except ValidationError as e:
        print(str(e))
        flash(message="Please fill in all required employee details", category='danger')
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    employee_ = await company_controller.add_employee(employee=new_employee)
    print(f"New Employee : {employee_}")
    branch = await company_controller.get_branch_by_id(branch_id=branch_id)
    branch.total_employees += 1
    updated_branch = await company_controller.update_company_branch(company_branch=branch)

    if employee_.email:

        new_user = await user_controller.get_by_email(email=employee_.email)

        if new_user:
            pass
        else:
            password = await user_controller.create_employee_password()
            password_hash = encryptor.create_hash(password=password)

            _new_user = User(uid=create_id(),
                             branch_id=branch_id,
                             company_id=user.company_id,
                             username=employee_.email,
                             email=employee_.email,
                             password_hash=password_hash,
                             is_employee=True)

            new_employee_user = await user_controller.add_employee(user=_new_user)

            send_email_verification_link = await user_controller.send_verification_email(user=new_employee_user,
                                                                                         password=password)
        message = """
        Your Employee has successfully been added.
            We have sent an Email to your employee with their login details
            Your Employee also need to click a link on the email to verify their email address            
        """
        flash(message=message, category="success")
        return redirect(url_for('company.get_branch', branch_id=branch_id))

    message = "We where unable to add your employee please try again if the problem persists please notify admin"

    flash(message=message, category="danger")
    return redirect(url_for('company.get_branch', branch_id=branch_id))


