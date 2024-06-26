from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError
from asyncio import gather

from src.logger import init_logger
from src.authentication import login_required
from src.database.models.bank_accounts import BankAccount
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.models.covers import ClientPersonalInformation, PolicyRegistrationData, InsuredParty
from src.database.models.users import User
from src.main import company_controller

clients_route = Blueprint('clients', __name__)
error_logger = init_logger('clients')


@clients_route.get('/admin/employees/client/<string:uid>')
@login_required
async def get_client(user: User, uid: str):
    """
    Retrieve client data and render the template.
    :param user: The current user
    :param uid: The unique ID of the client
    :return: Rendered template
    """
    # Retrieve all necessary data in parallel
    company_branches_task = company_controller.get_company_branches(company_id=user.company_id)
    policy_holder_task = company_controller.get_policy_holder(uid=uid)
    beneficiaries_task = company_controller.get_beneficiaries(
        policy_number=None)  # Assuming it's independent of policy number
    plan_covers_task = company_controller.get_company_covers(company_id=user.company_id)
    countries_task = company_controller.get_countries()
    policy_data_task = company_controller.get_policy_data(uid=None)  # Assuming it's independent of policy UID
    payment_methods_task = company_controller.get_payment_methods()

    # Wait for all parallel tasks to complete
    (company_branches, policy_holder, beneficiaries,
     plan_covers, countries, policy_data, payment_methods) = await gather(
        company_branches_task, policy_holder_task, beneficiaries_task,
        plan_covers_task, countries_task, policy_data_task, payment_methods_task
    )

    # Prepare the context dictionary
    context = {
        'user': user,
        'company_branches': company_branches,
        'plan_covers': plan_covers,
        'policy_holder': policy_holder,
        'policy_data': policy_data,
        'countries': countries,
        'payment_methods': payment_methods,
        'beneficiaries': beneficiaries
    }

    # Additional data retrieval if necessary
    if policy_holder.bank_account_id:
        context['bank_account'] = await company_controller.get_bank_account(
            bank_account_id=policy_holder.bank_account_id)
    if policy_holder.address_id:
        context['address'] = await company_controller.get_address(address_id=policy_holder.address_id)
    if policy_holder.postal_id:
        context['postal_address'] = await company_controller.get_postal_address(postal_id=policy_holder.postal_id)
    if policy_holder.contact_id:
        context['contact'] = await company_controller.get_contact(contact_id=policy_holder.contact_id)

    # Render the template with the context
    return render_template('admin/clients/client_editor.html', **context)


@clients_route.get('/admin/employees/clients')
@login_required
async def get_clients(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    plan_covers = await company_controller.get_company_covers(company_id=user.company_id)
    policy_holders_list = await company_controller.get_policy_holders(company_id=user.company_id)
    countries = await company_controller.get_countries()
    policy_holder = {}

    context = dict(user=user, company_branches=company_branches, plan_covers=plan_covers, countries=countries,
                   policy_holder=policy_holder, policy_holders_list=policy_holders_list)

    return render_template('admin/clients/clients.html', **context)



@clients_route.post('/admin/employees/clients/new-clients')
@login_required
async def add_client(user: User):
    """

    :param user:
    :return:
    """
    try:
        policy_holder: ClientPersonalInformation = ClientPersonalInformation(**request.form)
        policy_holder.insured_party = str(InsuredParty.POLICY_HOLDER.value)
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Unable to create or update client please provide all required details", category="danger")
        return redirect(url_for('clients.get_clients'))

    plan_cover = await company_controller.get_plan_cover(
        company_id=user.company_id, plan_number=policy_holder.plan_number)

    policy = PolicyRegistrationData(uid=policy_holder.uid,
                                    branch_id=policy_holder.branch_id,
                                    company_id=policy_holder.company_id,
                                    plan_number=policy_holder.plan_number,
                                    policy_type=plan_cover.plan_type,
                                    total_premiums=plan_cover.premium_costs)

    policy_holder.policy_number = policy.policy_number
    policy_holder = await company_controller.add_policy_holder(policy_holder=policy_holder)

    policy_ = await company_controller.add_policy_data(policy_data=policy)

    message = "Successfully created new client please remember to add family members"
    flash(message=message, category="success")
    return redirect(url_for('clients.get_clients'))


@clients_route.post('/admin/employees/clients/policy-editor')
@login_required
async def edit_policy_details(user: User):
    """

    :param user:
    :return:
    """
    try:
        print("inside editor")

        policy_data = PolicyRegistrationData(**request.form)
        uid = policy_data.uid
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="there was an error trying to edit policy data", category="danger")
        return redirect(url_for("clients.get_clients"))

    policy_ = await company_controller.add_policy_data(policy_data=policy_data)
    print(policy_)

    flash(message="Successfully updated Policy Data", category="success")
    return redirect(url_for("clients.get_client", uid=uid))


@clients_route.post('/admin/employees/client/policy/<string:policy_number>/add-beneficiary-dependent')
@login_required
async def add_beneficiary_dependent(user: User, policy_number: str):
    """

    :param policy_number:
    :param user:
    :return:
    """
    try:
        policy_data = await company_controller.get_policy_with_policy_number(policy_number=policy_number)
        beneficiary_data = ClientPersonalInformation(**request.form)

    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Error adding beneficiary", category="danger")
        return redirect(url_for('clients.get_clients'))

    new_beneficiary = await company_controller.add_policy_holder(policy_holder=beneficiary_data)

    flash(message="Successfully updated policy", category="success")
    return redirect(url_for('clients.get_client', uid=policy_data.uid))


@clients_route.post('/admin/employees/client/add-bank-account/<string:uid>')
@login_required
async def add_bank_account(user: User, uid: str):
    """

    :param user:
    :return:
    """
    try:
        client_bank_account = BankAccount(**request.form)
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Error adding Bank Account please provide all details", category="danger")
        return url_for('clients.get_client', uid=uid)

    stored_bank_account = await company_controller.add_bank_account(bank_account=client_bank_account)
    if stored_bank_account:
        client_personal_data = await company_controller.get_policy_holder(uid=uid)
        client_personal_data.bank_account_id = stored_bank_account.bank_account_id
        updated_client_data = await company_controller.add_policy_holder(policy_holder=client_personal_data)
        if updated_client_data:
            flash(message="successfully updated client bank account", category="success")
            return redirect(url_for('clients.get_client', uid=uid))

    flash(message="error trying to update client bank account please try again later", category="danger")
    return redirect(url_for('clients.get_client', uid=uid))


@clients_route.post('/admin/employees/client/address/<string:uid>')
@login_required
async def add_address(user: User, uid: str):
    """

    :param user:
    :param uid:
    :return:
    """
    try:
        client_address = Address(**request.form)
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Error adding Address please provide all details", category="danger")
        return url_for('clients.get_client', uid=uid)

    stored_address = await company_controller.add_update_address(address=client_address)
    if stored_address.address_id:
        client_personal_data = await company_controller.get_policy_holder(uid=uid)
        client_personal_data.address_id = stored_address.address_id
        updated_client_data = await company_controller.add_policy_holder(policy_holder=client_personal_data)
        if updated_client_data:
            flash(message="successfully updated client address", category="success")
            return redirect(url_for('clients.get_client', uid=uid))

    flash(message="error trying to update client address please try again later", category="danger")
    return redirect(url_for('clients.get_client', uid=uid))


@clients_route.post('/admin/employees/client/postal-address/<string:uid>')
@login_required
async def add_postal_address(user: User, uid: str):
    """

    :param user:
    :param uid:
    :return:
    """
    try:
        client_postal_address = PostalAddress(**request.form)
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Error adding Address please provide all details", category="danger")
        return url_for('clients.get_client', uid=uid)

    stored_postal_address = await company_controller.add_postal_address(postal_address=client_postal_address)
    if stored_postal_address.postal_id:
        client_personal_data = await company_controller.get_policy_holder(uid=uid)
        client_personal_data.postal_id = stored_postal_address.postal_id
        updated_client_data = await company_controller.add_policy_holder(policy_holder=client_personal_data)
        if updated_client_data:
            flash(message="successfully updated client postal address", category="success")
            return redirect(url_for('clients.get_client', uid=uid))

    flash(message="error trying to update client postal address please try again later", category="danger")
    return redirect(url_for('clients.get_client', uid=uid))


@clients_route.post('/admin/employees/client/contacts/<string:uid>')
@login_required
async def add_contacts(user: User, uid: str):
    """

    :param user:
    :param uid:
    :return:
    """
    try:
        client_contacts = Contacts(**request.form)
    except ValidationError as e:
        error_logger.error(str(e))
        flash(message="Error adding Address Contact Details", category="danger")
        return url_for('clients.get_client', uid=uid)

    stored_contacts = await company_controller.add_contacts(contact=client_contacts)
    if stored_contacts.contact_id:
        client_personal_data = await company_controller.get_policy_holder(uid=uid)
        client_personal_data.contact_id = stored_contacts.contact_id
        updated_client_data = await company_controller.add_policy_holder(policy_holder=client_personal_data)
        if updated_client_data:
            flash(message="successfully updated client contact details", category="success")
            return redirect(url_for('clients.get_client', uid=uid))

    flash(message="error trying to update client contacts please try again later", category="danger")
    return redirect(url_for('clients.get_client', uid=uid))
