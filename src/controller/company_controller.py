import random
from datetime import datetime
from flask import Flask
from sqlalchemy.exc import OperationalError

from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation, PaymentMethods, InsuredParty
from src.database.sql.covers import PolicyRegistrationDataORM, ClientPersonalInformationORM
from src.database.sql.bank_account import BankAccountORM
from src.database.models.bank_accounts import BankAccount
from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM, CoverPlanDetailsORM
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails, CoverPlanDetails
from src.controller import Controllers, error_handler


class CompanyController(Controllers):

    def __init__(self):
        super().__init__()

        self.countries = [
            "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde",
            "Cameroon", "Central African Republic", "Chad", "Comoros",
            "Democratic Republic of the Congo", "Republic of the Congo", "Djibouti",
            "Equatorial Guinea", "Eritrea", "Ethiopia", "Gabon", "Gambia", "Ghana",
            "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia",
            "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Mozambique",
            "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe",
            "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa",
            "South Sudan", "Sudan", "Swaziland", "Tanzania", "Togo", "Uganda",
            "Zambia", "Zimbabwe"
        ]

    def init_app(self, app: Flask):
        super().init_app(app=app)

    @error_handler
    async def register_company(self, company: Company) -> Company | None:
        """

        :param company:
        :return:
        """
        with self.get_session() as session:
            company_name = company.company_name.strip().lower()
            company_list = session.query(CompanyORM).filter(CompanyORM.company_name == company_name).all()
            if company_list:
                return None
            company_orm = CompanyORM(**company.dict())
            session.add(company_orm)
            session.commit()

            return company

    @error_handler
    async def get_company_details(self, company_id: str) -> Company | None:
        with self.get_session() as session:
            company_orm = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()
            if isinstance(company_orm, CompanyORM):
                return Company(**company_orm.to_dict())
            return None

    @error_handler
    async def add_company_branch(self, company_branch: CompanyBranches) -> CompanyBranches | None:
        """

        :param company_branch:
        :return:
        """

        with self.get_session() as session:
            _branch_name = company_branch.branch_name.lower().strip()
            company_branches_orm = session.query(CompanyBranchesORM).filter(
                CompanyBranchesORM.branch_name == _branch_name.casefold()).first()
            if isinstance(company_branches_orm, CompanyBranchesORM):
                return None
            session.add(CompanyBranchesORM(**company_branch.dict()))
            session.commit()
            return company_branch

    @error_handler
    async def update_company_branch(self, company_branch: CompanyBranches) -> CompanyBranches | None:
        """

        :param company_branch:
        :return:
        """
        with self.get_session() as session:
            branch_orm = session.query(CompanyBranchesORM).filter_by(branch_id=company_branch.branch_id).first()
            if branch_orm:
                # Update the attributes of the retrieved branch record
                branch_orm.branch_name = company_branch.branch_name
                branch_orm.company_id = company_branch.company_id
                branch_orm.branch_description = company_branch.branch_description
                branch_orm.date_registered = company_branch.date_registered
                branch_orm.total_clients = company_branch.total_clients
                branch_orm.total_employees = company_branch.total_employees
                branch_orm.address_id = company_branch.address_id
                branch_orm.contact_id = company_branch.contact_id
                branch_orm.postal_id = company_branch.postal_id
                branch_orm.bank_account_id = company_branch.bank_account_id

                session.commit()
                return company_branch
            return None

    @error_handler
    async def get_company_branches(self, company_id: str) -> list[CompanyBranches]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            company_branches_orm = session.query(CompanyBranchesORM).filter(
                CompanyBranchesORM.company_id == company_id).all()
            return [CompanyBranches(**branch_orm.to_dict()) for branch_orm in company_branches_orm
                    if isinstance(branch_orm, CompanyBranchesORM)]

    @error_handler
    async def get_branch_by_id(self, branch_id: str) -> CompanyBranches | None:
        """

        :param branch_id:
        :return:
        """
        with self.get_session() as session:
            branch_orm = session.query(CompanyBranchesORM).filter(CompanyBranchesORM.branch_id == branch_id).first()

            if not isinstance(branch_orm, CompanyBranchesORM):
                return None
            return CompanyBranches(**branch_orm.to_dict())

    @error_handler
    async def get_employee_roles(self, company_id: str) -> list[str]:
        """

        :param company_id:
        :return:
        """
        return EmployeeRoles.get_all_roles()

    @error_handler
    async def add_update_address(self, address: Address) -> Address | None:
        """

        :param address:
        :return:
        """
        with self.get_session() as session:
            branch_address_orm = session.query(AddressORM).filter_by(address_id=address.address_id).first()

            if isinstance(branch_address_orm, AddressORM):
                branch_address_orm.street = address.street
                branch_address_orm.city = address.city
                branch_address_orm.state_province = address.state_province
                branch_address_orm.postal_code = address.postal_code
                session.commit()
                return address
            try:
                session.add(AddressORM(**address.dict()))
                session.commit()
                return address
            except OperationalError as e:
                print(str(e))
                return None

    @error_handler
    async def get_address(self, address_id: str) -> Address | None:
        with self.get_session() as session:
            branch_address = session.query(AddressORM).filter_by(address_id=address_id).first()
            if isinstance(branch_address, AddressORM):
                return Address(**branch_address.to_dict())
            return None

    @error_handler
    async def add_postal_address(self, postal_address: PostalAddress) -> PostalAddress | None:
        """

        :param postal_address:
        :return:
        """
        with self.get_session() as session:
            _postal_id = postal_address.postal_id
            branch_postal_orm = session.query(PostalAddressORM).filter_by(postal_id=_postal_id).first()
            if isinstance(branch_postal_orm, PostalAddressORM):
                branch_postal_orm.address_line_1 = postal_address.address_line_1
                branch_postal_orm.town_city = postal_address.town_city
                branch_postal_orm.province = postal_address.province
                branch_postal_orm.country = postal_address.country
                branch_postal_orm.postal_code = postal_address.postal_code
                session.commit()
                return postal_address

            session.add(PostalAddressORM(**postal_address.dict()))
            session.commit()
            return postal_address

    @error_handler
    async def get_postal_address(self, postal_id: str) -> PostalAddress | None:
        """

        :param postal_id:
        :return:
        """
        with self.get_session() as session:
            postal_address_orm = session.query(PostalAddressORM).filter_by(postal_id=postal_id).first()
            if isinstance(postal_address_orm, PostalAddressORM):
                return PostalAddress(**postal_address_orm.to_dict())
            return None

    @error_handler
    async def add_contacts(self, contact: Contacts) -> Contacts | None:
        """
        Add branch contacts to the database.

        :param contact: Instance of Contacts containing contact details.
        :return: Added Contacts instance if successful, None otherwise.
        """
        with self.get_session() as session:
            contact_orm = session.query(ContactsORM).filter_by(contact_id=contact.contact_id).first()
            if isinstance(contact_orm, ContactsORM):
                # Update existing contact details
                contact_orm.cell = contact.cell
                contact_orm.tel = contact.tel
                contact_orm.email = contact.email
                contact_orm.facebook = contact.facebook
                contact_orm.twitter = contact.twitter
                contact_orm.whatsapp = contact.whatsapp
                session.commit()
                return contact
            # Add new contact details
            session.add(ContactsORM(**contact.dict()))
            session.commit()
            return contact

    @error_handler
    async def get_contact(self, contact_id: str) -> Contacts | None:
        """
        Retrieve branch contact details from the database.

        :param contact_id: The ID of the branch whose contact details to retrieve.
        :return: Contacts instance if found, None otherwise.
        """
        with self.get_session() as session:
            # Query the database for the contact details associated with the given branch_id
            branch_contact_orm = session.query(ContactsORM).filter_by(contact_id=contact_id).first()

            if isinstance(branch_contact_orm, ContactsORM):
                # If contact details exist, create a Contacts instance from the retrieved data
                branch_contact = Contacts(**branch_contact_orm.to_dict())
                return branch_contact

            return None

    @error_handler
    async def add_bank_account(self, bank_account: BankAccount) -> BankAccount | None:
        """
        Add or update a branch bank account in the database.

        :param bank_account: Instance of BankAccount containing bank account details.
        :return: Added or updated BankAccount instance if successful, None otherwise.
        """
        with self.get_session() as session:
            bank_account_orm = session.query(BankAccountORM).filter_by(
                bank_account_id=bank_account.bank_account_id).first()

            if isinstance(bank_account_orm, BankAccountORM):
                # If the bank account already exists, update its details
                bank_account_orm.account_holder = bank_account.account_holder
                bank_account_orm.account_number = bank_account.account_number
                bank_account_orm.bank_name = bank_account.bank_name
                bank_account_orm.branch = bank_account.branch
                bank_account_orm.account_type = bank_account.account_type
                session.commit()
                return bank_account
            try:
                # If the bank account does not exist, add it to the database
                session.add(BankAccountORM(**bank_account.dict()))
                session.commit()
                return bank_account
            except OperationalError as e:
                print(str(e))
                session.rollback()
                return None

    @error_handler
    async def get_bank_account(self, bank_account_id: str) -> BankAccount | None:
        """

        :param bank_account_id:
        :return:
        """
        with self.get_session() as session:
            bank_account_orm = session.query(BankAccountORM).filter_by(bank_account_id=bank_account_id).first()

            if isinstance(bank_account_orm, BankAccountORM):
                return BankAccount(**bank_account_orm.to_dict())
            return None

    @error_handler
    async def add_employee(self, employee: EmployeeDetails) -> tuple[bool, EmployeeDetails | None]:
        """

        :param employee:
        :return:
        """
        with self.get_session() as session:
            _id_number = employee.id_number
            employee_orm = session.query(EmployeeORM).filter_by(id_number=_id_number).first()
            if isinstance(employee_orm, EmployeeORM):
                employee_orm.full_names = employee.full_names
                employee_orm.last_name = employee.last_name
                employee_orm.role = employee.role
                employee_orm.id_number = employee.id_number
                employee_orm.email = employee.email
                employee_orm.contact_number = employee.contact_number
                employee_orm.position = employee.position
                employee_orm.date_of_birth = datetime.strptime(employee.date_of_birth, '%Y-%m-%d').date()
                employee_orm.date_joined = datetime.strptime(employee.date_joined, '%Y-%m-%d').date()
                employee_orm.salary = employee.salary
                employee_orm.is_active = employee.is_active
                employee_orm.address_id = employee.address_id
                employee_orm.postal_id = employee.postal_id
                employee_orm.bank_account_id = employee.bank_account_id
                employee_orm.contact_id = employee.contact_id

                session.commit()
                return False, employee
            try:
                session.add(EmployeeORM(**employee.dict()))
                session.commit()
            except OperationalError as e:
                session.rollback()
                return False, None
            return True, employee

    @error_handler
    async def get_branch_employees(self, branch_id: str) -> list[EmployeeDetails]:
        """

        :param branch_id:
        :return:
        """
        with self.get_session() as session:
            employees_orm = session.query(EmployeeORM).filter_by(branch_id=branch_id).all()
            return [EmployeeDetails(**employee.to_dict()) for employee in employees_orm if
                    isinstance(employee, EmployeeORM)]

    @error_handler
    async def get_employee(self, employee_id: str) -> EmployeeDetails | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            employee_orm = session.query(EmployeeORM).filter_by(employee_id=employee_id).first()
            if isinstance(employee_orm, EmployeeORM):
                return EmployeeDetails(**employee_orm.to_dict())
            return None

    async def get_company_employees(self, company_id: str) -> list[EmployeeDetails]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            employees_orm_list = session.query(EmployeeORM).filter_by(company_id=company_id).all()
            return [EmployeeDetails(**employee_orm.to_dict()) for employee_orm in employees_orm_list
                    if isinstance(employee_orm, EmployeeORM)]

    async def create_plan_cover(self, plan_cover: CoverPlanDetails) -> CoverPlanDetails:
        """
        Create or update a cover plan in the database.

        :param plan_cover: CoverPlanDetails instance
        :return: CoverPlanDetails instance
        """
        with self.get_session() as session:
            _plan_name = plan_cover.plan_name.casefold()
            company_id = plan_cover.company_id
            cover_plan_orm = session.query(CoverPlanDetailsORM).filter_by(plan_name=_plan_name,
                                                                          company_id=company_id).first()

            if cover_plan_orm:  # If cover plan exists, update its fields
                # cover_plan_orm.plan_number = plan_cover.plan_number
                cover_plan_orm.plan_type = plan_cover.plan_type
                cover_plan_orm.benefits = plan_cover.benefits
                cover_plan_orm.coverage_amount = plan_cover.coverage_amount
                cover_plan_orm.premium_costs = plan_cover.premium_costs
                cover_plan_orm.additional_details = plan_cover.additional_details
                cover_plan_orm.terms_and_conditions = plan_cover.terms_and_conditions
                cover_plan_orm.inclusions = plan_cover.inclusions
                cover_plan_orm.exclusions = plan_cover.exclusions
                cover_plan_orm.contact_information = plan_cover.contact_information
            else:  # If cover plan doesn't exist, create a new entry
                cover_plan_orm = CoverPlanDetailsORM(**plan_cover.dict())

            session.add(cover_plan_orm)
            session.commit()

            return plan_cover

    async def get_company_covers(self, company_id: str) -> list[CoverPlanDetails]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            cover_details_list = session.query(CoverPlanDetailsORM).filter_by(company_id=company_id).all()
            return [CoverPlanDetails(**plan.to_dict()) for plan in cover_details_list
                    if isinstance(plan, CoverPlanDetailsORM)]

    async def get_plan_cover(self, company_id: str, plan_number: str) -> CoverPlanDetails | None:
        """

        :param company_id:
        :param plan_number:
        :return:
        """
        with self.get_session() as session:
            plan_cover_orm = session.query(CoverPlanDetailsORM).filter_by(company_id=company_id,
                                                                          plan_number=plan_number).first()
            if isinstance(plan_cover_orm, CoverPlanDetailsORM):
                return CoverPlanDetails(**plan_cover_orm.to_dict())
            return None

    async def get_plan_subscribers(self, plan_number: str) -> list[PolicyRegistrationData]:
        """

        :param plan_number:
        :return:
        """
        with self.get_session() as session:
            plan_subscribers = session.query(PolicyRegistrationDataORM).filter_by(plan_number=plan_number).all()
            return [PolicyRegistrationData(**subscriber.to_dict()) for subscriber in plan_subscribers
                    if isinstance(subscriber, PolicyRegistrationDataORM)]

    async def get_policy_holders(self, company_id: str) -> list[ClientPersonalInformation]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            policy_holder = InsuredParty.POLICY_HOLDER.value
            policy_holders_list = session.query(ClientPersonalInformationORM).filter_by(company_id=company_id,
                                                                                        insured_party=policy_holder).all()
            return [ClientPersonalInformation(**holder.to_dict()) for holder in policy_holders_list]

    async def get_policy_holder(self, uid: str) -> ClientPersonalInformation | None:
        with self.get_session() as session:
            policy_holder_orm = session.query(ClientPersonalInformationORM).filter_by(uid=uid).first()
            if isinstance(policy_holder_orm, ClientPersonalInformationORM):
                return ClientPersonalInformation(**policy_holder_orm.to_dict())
            return None

    async def get_policy_data(self, uid: str):
        with self.get_session() as session:
            policy_data_orm = session.query(PolicyRegistrationDataORM).filter_by(uid=uid).first()
            if isinstance(policy_data_orm, PolicyRegistrationDataORM):
                return PolicyRegistrationData(**policy_data_orm.to_dict())
            return None

    async def get_beneficiaries(self, policy_number: str):
        """

        :param policy_number:
        :return:
        """
        with self.get_session() as session:
            beneficiaries_list_orm = session.query(ClientPersonalInformationORM).filter_by(
                policy_number=policy_number).all()
            return [ClientPersonalInformation(**client.to_dict()) for client in beneficiaries_list_orm]

    async def get_payment_methods(self) -> list[str]:
        return PaymentMethods.get_payment_methods()

    async def add_policy_holder(self, policy_holder: ClientPersonalInformation) -> ClientPersonalInformation:
        """
        Add or update a policy holder in the database.

        :param policy_holder: ClientPersonalInformation instance
        :return: None
        """
        with self.get_session() as session:
            uid = policy_holder.uid
            branch_id = policy_holder.branch_id
            company_id = policy_holder.company_id

            policy_holder_orm = session.query(ClientPersonalInformationORM).filter_by(
                uid=uid).first()

            if policy_holder_orm:
                # Update all fields for the existing policy holder
                policy_holder_orm.branch_id = branch_id
                policy_holder_orm.company_id = company_id
                policy_holder_orm.title = policy_holder.title
                policy_holder_orm.full_names = policy_holder.full_names
                policy_holder_orm.surname = policy_holder.surname
                policy_holder_orm.id_number = policy_holder.id_number
                policy_holder_orm.date_of_birth = policy_holder.date_of_birth
                policy_holder_orm.nationality = policy_holder.nationality
                policy_holder_orm.policy_number = policy_holder.policy_number
                policy_holder_orm.insured_party = policy_holder.insured_party
                policy_holder_orm.address_id = policy_holder.address_id
                policy_holder_orm.contact_id = policy_holder.contact_id
                policy_holder_orm.postal_id = policy_holder.postal_id
                policy_holder_orm.bank_account_id = policy_holder.bank_account_id
            else:
                # Create a new policy holder entry
                policy_holder_orm = ClientPersonalInformationORM(**policy_holder.dict())

            session.add(policy_holder_orm)
            session.commit()
            return policy_holder

    async def add_policy_data(self, policy_data: PolicyRegistrationData) -> PolicyRegistrationData:
        """
        Add or update policy data in the database.

        :param policy_data: PolicyRegistrationData instance
        :return: PolicyRegistrationData instance
        """
        with self.get_session() as session:
            uid = policy_data.uid
            branch_id = policy_data.branch_id
            company_id = policy_data.company_id

            # Query the database to check if the policy data already exists
            policy_data_orm = session.query(PolicyRegistrationDataORM).filter_by(
                uid=uid, company_id=company_id).first()

            if policy_data_orm:
                # Update all fields for the existing policy data
                policy_data_orm.branch_id = branch_id
                policy_data_orm.company_id = company_id
                policy_data_orm.policy_number = policy_data.policy_number
                policy_data_orm.plan_number = policy_data.plan_number
                policy_data_orm.policy_type = policy_data.policy_type
                policy_data_orm.total_family_members = policy_data.total_family_members
                policy_data_orm.total_premiums = policy_data.total_premiums
                policy_data_orm.payment_code_reference = policy_data.payment_code_reference
                policy_data_orm.date_activated = policy_data.date_activated
                policy_data_orm.first_premium_date = policy_data.first_premium_date
                policy_data_orm.payment_day = policy_data.payment_day
                policy_data_orm.client_signature = policy_data.client_signature
                policy_data_orm.employee_signature = policy_data.employee_signature
                policy_data_orm.payment_method = policy_data.payment_method
                policy_data_orm.policy_active = policy_data.policy_active
            else:
                # Create a new policy data entry
                policy_data_orm = PolicyRegistrationDataORM(**policy_data.dict())

            session.add(policy_data_orm)
            session.commit()

            return policy_data

    async def get_countries(self):
        return self.countries

    async def get_policy_with_policy_number(self, policy_number: str) -> PolicyRegistrationData | None:
        """

        :param policy_number:
        :return:
        """
        with self.get_session() as session:
            policy_data_orm = session.query(PolicyRegistrationDataORM).filter_by(policy_number=policy_number).first()
            if isinstance(policy_data_orm, PolicyRegistrationDataORM):
                return PolicyRegistrationData(**policy_data_orm.to_dict())
            return None

    async def search_policies_by_id_number(self, id_number: str) -> list[PolicyRegistrationData]:
        """

        :param id_number:
        :return:
        """
        with self.get_session() as session:
            client_data_orm = session.query(ClientPersonalInformationORM).filter_by(id_number=id_number).first()
            if isinstance(client_data_orm, ClientPersonalInformationORM):
                policy_number = client_data_orm.policy_number
                policy_data_orm_list = session.query(PolicyRegistrationDataORM).filter_by(policy_number=policy_number).all()
                return [PolicyRegistrationData(**policy_orm.to_dict()) for policy_orm in policy_data_orm_list
                        if isinstance(policy_orm, PolicyRegistrationDataORM)]
            return []

    async def search_policies_by_policy_number(self, policy_number: str) -> list[PolicyRegistrationData]:
        """

        :param policy_number:
        :return:
        """
        with self.get_session() as session:
            policy_data_orm_list = session.query(PolicyRegistrationDataORM).filter_by(policy_number=policy_number).all()
            return [PolicyRegistrationData(**policy_orm.to_dict()) for policy_orm in policy_data_orm_list
                    if isinstance(policy_orm, PolicyRegistrationDataORM)]

    async def search_policies_by_policy_holder_name(self, policy_holder_name: str) -> list[PolicyRegistrationData]:
        '''
        Search for policies by policy holder name.
        :param policy_holder_name: The name of the policy holder to search for.
        :return: List of policies matching the policy holder name.
        '''
        with self.get_session() as session:
            # Perform a single query to fetch policies by policy holder name
            policies_orm = session.query(PolicyRegistrationDataORM) \
                .join(ClientPersonalInformationORM,
                      ClientPersonalInformationORM.policy_number == PolicyRegistrationDataORM.policy_number) \
                .filter(ClientPersonalInformationORM.full_names == policy_holder_name) \
                .all()

            # Convert ORM objects to PolicyRegistrationData objects
            return [PolicyRegistrationData(**policy_orm.to_dict()) for policy_orm in policies_orm]
