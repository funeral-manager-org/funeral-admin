from datetime import datetime

from flask import Flask
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload

from src.controller.messaging_controller import MessagingController
from src.controller import Controllers, error_handler
from src.database.models.bank_accounts import BankAccount
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails, CoverPlanDetails
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation, PaymentMethods, InsuredParty
from src.database.sql.bank_account import BankAccountORM
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM, CoverPlanDetailsORM
from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
from src.database.sql.covers import PolicyRegistrationDataORM, ClientPersonalInformationORM


class CoversController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        """

        :param app:
        :return:
        """
        pass

    async def do_send_upcoming_payment_reminders(self, company_id: str):
        """
            TODO -
                check if there is enough sms credits
                open the cover record and get client details
                send sms reminder

        :param company_id:
        :return:
        """
        pass

    async def send_payment_reminders(self, messaging_controller: MessagingController):
        """
        TODO - this method needs to be scheduled to run once every week

            This Method will go through all the covers and all clients
            then send payment reminders to every client
        :return:
        """
        with self.get_session() as session:
            companies_orm_list = session.query(CompanyORM).all()
            companies_list = [Company(**company_orm.to_dict()) for company_orm in companies_orm_list]

        for company in companies_list:
            sms_settings = await messaging_controller.sms_service.get_sms_settings(company_id=company.company_id)

            if sms_settings.enable_sms_notifications and sms_settings.upcoming_payments_notifications:
                self.logger.info(f"Sending Payment Reminders for company : {company.company_name}")
                await self.do_send_upcoming_payment_reminders(company_id=company.company_id)
