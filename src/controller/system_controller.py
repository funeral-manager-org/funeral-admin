from datetime import datetime

from flask import Flask
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload

from src.database.models.subscriptions import SubscriptionDetails
from src.database.sql.subscriptions import SubscriptionsORM
from src.controller import Controllers, error_handler
from src.database.models.bank_accounts import BankAccount
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails, CoverPlanDetails
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation, PaymentMethods, InsuredParty
from src.database.sql.bank_account import BankAccountORM
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM, CoverPlanDetailsORM
from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
from src.database.sql.covers import PolicyRegistrationDataORM, ClientPersonalInformationORM


class SystemController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def get_all_companies(self) -> list[Company]:
        """
            will return a list of all companies registered on the system
        :return:
        """
        with self.get_session() as session:
            companies_orm_list = session.query(CompanyORM).all()
            return [Company(**company_orm.to_dict()) for company_orm in companies_orm_list if isinstance(company_orm, CompanyORM)]

    async def get_subscriptions(self, company_id: str):
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            subscriptions_orm_list = session.query(SubscriptionsORM).all()
            return [SubscriptionDetails(**sub_orm.to_dict()) for sub_orm in subscriptions_orm_list]

