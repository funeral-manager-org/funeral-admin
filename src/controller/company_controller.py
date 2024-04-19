import random

from flask import Flask

from src.database.sql.contacts import AddressORM
from src.database.models.contacts import Address
from src.database.sql.companies import CompanyORM, CompanyBranchesORM
from src.database.models.companies import Company, CompanyBranches
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

    async def update_company_branch(self, company_branch: CompanyBranches):
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
