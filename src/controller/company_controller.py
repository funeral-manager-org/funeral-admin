import random
from datetime import datetime
from flask import Flask

from src.database.sql.bank_account import BankAccountORM
from src.database.models.bank_accounts import BankAccount
from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails
from src.controller import Controllers, error_handler


class CompanyController(Controllers):

    def __init__(self):
        super().__init__()
        pass

    def init_app(self, app: Flask):
        super().init_app(app=app)

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

    async def get_company_details(self, company_id: str) -> Company | None:
        with self.get_session() as session:
            company_orm = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()
            if isinstance(company_orm, CompanyORM):
                return Company(**company_orm.to_dict())
            return None

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

    async def get_employee_roles(self, company_id: str) -> list[str]:
        """

        :param company_id:
        :return:
        """
        return EmployeeRoles.get_all_roles()

    async def add_update_branch_address(self, branch_address: Address) -> Address:
        """

        :param branch_address:
        :return:
        """
        with self.get_session() as session:
            branch_address_orm = session.query(AddressORM).filter_by(address_id=branch_address.address_id).first()

            if isinstance(branch_address_orm, AddressORM):
                branch_address_orm.street = branch_address.street
                branch_address_orm.city = branch_address.city
                branch_address_orm.state_province = branch_address.state_province
                branch_address_orm.postal_code = branch_address.postal_code
                session.commit()
                return branch_address

            session.add(AddressORM(**branch_address.dict()))
            session.commit()
            return branch_address

    async def get_branch_address(self, address_id: str) -> Address | None:
        with self.get_session() as session:
            branch_address = session.query(AddressORM).filter_by(address_id=address_id).first()
            if isinstance(branch_address, AddressORM):
                return Address(**branch_address.to_dict())
            return None

    async def add_branch_postal_address(self, branch_postal_address: PostalAddress) -> PostalAddress | None:
        """

        :param branch_postal_address:
        :return:
        """
        with self.get_session() as session:
            _postal_id = branch_postal_address.postal_id
            branch_postal_orm = session.query(PostalAddressORM).filter_by(postal_id=_postal_id).first()
            if isinstance(branch_postal_orm, PostalAddressORM):
                branch_postal_orm.address_line_1 = branch_postal_address.address_line_1
                branch_postal_orm.town_city = branch_postal_address.town_city
                branch_postal_orm.province = branch_postal_address.province
                branch_postal_orm.country = branch_postal_address.country
                branch_postal_orm.postal_code = branch_postal_address.postal_code
                session.commit()
                return branch_postal_address

            session.add(PostalAddressORM(**branch_postal_address.dict()))
            session.commit()
            return branch_postal_address

    async def get_branch_postal_address(self, postal_id: str) -> PostalAddress | None:
        """

        :param postal_id:
        :return:
        """
        with self.get_session() as session:
            postal_address_orm = session.query(PostalAddressORM).filter_by(postal_id=postal_id).first()
            if isinstance(postal_address_orm, PostalAddressORM):
                return PostalAddress(**postal_address_orm.to_dict())
            return None

    async def add_branch_contacts(self, branch_contacts: Contacts) -> Contacts | None:
        """
        Add branch contacts to the database.

        :param branch_contacts: Instance of Contacts containing contact details.
        :return: Added Contacts instance if successful, None otherwise.
        """
        with self.get_session() as session:
            contact_orm = session.query(ContactsORM).filter_by(contact_id=branch_contacts.contact_id).first()
            if isinstance(contact_orm, ContactsORM):
                # Update existing contact details
                contact_orm.cell = branch_contacts.cell
                contact_orm.tel = branch_contacts.tel
                contact_orm.email = branch_contacts.email
                contact_orm.facebook = branch_contacts.facebook
                contact_orm.twitter = branch_contacts.twitter
                contact_orm.whatsapp = branch_contacts.whatsapp
                session.commit()
                return branch_contacts
            # Add new contact details
            session.add(ContactsORM(**branch_contacts.dict()))
            session.commit()
            return branch_contacts

    async def get_branch_contact(self, contact_id: str) -> Contacts | None:
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

    async def add_branch_bank_account(self, branch_bank_account: BankAccount) -> BankAccount | None:
        """
        Add or update a branch bank account in the database.

        :param branch_bank_account: Instance of BankAccount containing bank account details.
        :return: Added or updated BankAccount instance if successful, None otherwise.
        """
        with self.get_session() as session:
            bank_account_orm = session.query(BankAccountORM).filter_by(
                bank_account_id=branch_bank_account.bank_account_id).first()

            if isinstance(bank_account_orm, BankAccountORM):
                # If the bank account already exists, update its details
                bank_account_orm.account_holder = branch_bank_account.account_holder
                bank_account_orm.account_number = branch_bank_account.account_number
                bank_account_orm.bank_name = branch_bank_account.bank_name
                bank_account_orm.branch = branch_bank_account.branch
                bank_account_orm.account_type = branch_bank_account.account_type
                session.commit()
                return branch_bank_account

            # If the bank account does not exist, add it to the database
            session.add(BankAccountORM(**branch_bank_account.dict()))
            session.commit()
            return branch_bank_account

    async def get_branch_bank_account(self, bank_account_id: str) -> BankAccount | None:
        """

        :param bank_account_id:
        :return:
        """
        with self.get_session() as session:
            bank_account_orm = session.query(BankAccountORM).filter_by(bank_account_id=bank_account_id).first()

            if isinstance(bank_account_orm, BankAccountORM):
                return BankAccount(**bank_account_orm.to_dict())
            return None

    async def add_employee(self, employee: EmployeeDetails) -> EmployeeDetails | None:
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

                session.commit()
                return employee

            session.add(EmployeeORM(**employee.dict()))

            session.commit()

            return employee

    async def get_branch_employees(self, branch_id: str) -> list[EmployeeDetails]:
        """

        :param branch_id:
        :return:
        """
        with self.get_session() as session:
            employees_orm = session.query(EmployeeORM).filter_by(branch_id=branch_id).all()
            print("EMPLOYEE ORM")
            print(employees_orm)
            return [EmployeeDetails(**employee.to_dict()) for employee in employees_orm if
                    isinstance(employee, EmployeeORM)]

