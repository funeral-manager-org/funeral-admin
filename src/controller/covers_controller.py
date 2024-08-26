import datetime
from datetime import date

from dateutil.relativedelta import relativedelta
from flask import Flask, render_template
from sqlalchemy.orm import joinedload

from src.database.models.messaging import SMSCompose, RecipientTypes, EmailCompose
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company, CompanyBranches
from src.database.models.contacts import Contacts
from src.database.sql.companies import CompanyORM, CompanyBranchesORM
from src.database.sql.contacts import ContactsORM
from src.controller import Controllers, error_handler
from src.database.models.covers import Premiums, PolicyRegistrationData, ClientPersonalInformation, PremiumReceipt, \
    Claims
from src.database.sql.covers import PremiumsORM, PolicyRegistrationDataORM, ClientPersonalInformationORM, \
    PremiumReceiptORM, ClaimsORM


def next_due_date(start_date: date) -> date:
    """
    # TODO - refactor this is repetition
    Return the next due date on the same day of the next month.
    """
    return start_date + relativedelta(months=1)


class CoversController(Controllers):
    """
        cover controller is responsible
        with creating reports for employees so they know
        where to keep their attention in the company

    """

    def __init__(self):
        super().__init__()
        self.messaging_controller: MessagingController | None = None

    def init_app(self, app: Flask, messaging_controller: MessagingController):
        """
            pass
        :param app:
        :return:
        """
        super().init_app(app=app)
        self.messaging_controller = messaging_controller

    @error_handler
    async def add_update_premiums_payment(self, premium_payment: Premiums) -> Premiums:
        """

        :param premium_payment:
        :return:
        """
        with self.get_session() as session:
            premium_orm = session.query(PremiumsORM).filter_by(premium_id=premium_payment.premium_id).first()
            if isinstance(premium_orm, PremiumsORM):

                premium_orm.scheduled_payment_date = premium_payment.scheduled_payment_date
                premium_orm.payment_amount = premium_payment.payment_amount
                premium_orm.amount_paid = premium_payment.amount_paid
                premium_orm.date_paid = premium_payment.date_paid
                premium_orm.payment_method = premium_payment.payment_method
                premium_orm.payment_status = premium_payment.payment_status
                premium_orm.next_payment_amount = premium_payment.next_payment_amount
                premium_orm.next_payment_date = premium_payment.next_payment_date
                premium_orm.payment_frequency = premium_payment.payment_frequency

            else:
                payment_orm = PremiumsORM(**premium_payment.dict())
                session.add(payment_orm)

            return premium_payment

    @error_handler
    async def change_payment_status(self, status: str, premium_id: str):
        with self.get_session() as session:
            premium_orm: PremiumsORM = session.query(PremiumsORM).filter_by(premium_id=premium_id).first()
            premium_orm.payment_status = status

    @error_handler
    async def add_premium_receipt(self, receipt: PremiumReceipt) -> PremiumReceipt | None:
        with self.get_session() as session:
            if not receipt:
                return
            session.add(PremiumReceiptORM(**receipt.dict(exclude={'premium'})))
            return receipt

    @error_handler
    async def get_policy_data(self, policy_number: str) -> PolicyRegistrationData | None:
        with self.get_session() as session:
            policy_data_orm = (
                session.query(PolicyRegistrationDataORM)
                .filter_by(policy_number=policy_number)
                .options(joinedload(PolicyRegistrationDataORM.premiums))  # Load related premiums
                .first()
            )
            if isinstance(policy_data_orm, PolicyRegistrationDataORM):
                return PolicyRegistrationData(**policy_data_orm.to_dict())
            return None

    @error_handler
    async def get_branch_policy_data_list(self,
                                          branch_id: str,
                                          page: int = 0,
                                          count: int = 25) -> list[PolicyRegistrationData]:
        """
        **get_branch_policy_data_list**

        :param branch_id: ID of the branch
        :param page: Page number (default is 0)
        :param count: Number of items per page (default is 25)
        :return: List of PolicyRegistrationData
        """
        with self.get_session() as session:
            policy_data_orm_list = (
                session.query(PolicyRegistrationDataORM)
                .filter_by(branch_id=branch_id)
                .options(joinedload(PolicyRegistrationDataORM.premiums))
                .offset(page * count)
                .limit(count)
                .all()
            )
            return [PolicyRegistrationData(**policy_data_orm.to_dict())
                    for policy_data_orm in policy_data_orm_list or []
                    if isinstance(policy_data_orm, PolicyRegistrationDataORM)]

    @error_handler
    async def get_outstanding_branch_policy_data_list(self,
                                                      branch_id: str,
                                                      page: int = 0,
                                                      count: int = 25) -> list[PolicyRegistrationData]:
        """
            **get_outstanding_branch_policy_data_list**
        :param branch_id:
        :param page:
        :param count:
        :return:
        """
        with self.get_session() as session:
            policy_data_orm_list = (
                session.query(PolicyRegistrationDataORM)
                .filter_by(branch_id=branch_id)
                .options(joinedload(PolicyRegistrationDataORM.premiums))
                .offset(page * count)
                .all()
            )
            policy_reg_data: list[PolicyRegistrationData] = [PolicyRegistrationData(**policy_data_orm.to_dict())
                                                             for policy_data_orm in policy_data_orm_list or []
                                                             if isinstance(policy_data_orm, PolicyRegistrationDataORM)]
            # filter out outstanding policies and return policies upto the limit = count
            return [policy for policy in policy_reg_data if policy.out_standing][:count]

    @error_handler
    async def create_forecasted_premiums(self, policy_number: str, total: int = 12):
        """
            by default this method will create at least 12 premium records in advance
        :return:
        """
        policy_data: PolicyRegistrationData = await self.get_policy_data(policy_number=policy_number)

        with self.get_session() as session:
            today = datetime.datetime.now().date()
            # sets payment day as the 1st of next month
            # TODO Maybe needs a refactor Premium can calculate its own Dates
            scheduled_payment_date = today.replace(day=1) + relativedelta(months=1)

            for i in range(total):
                # advance payment day to the month following the present
                scheduled_payment_date = next_due_date(start_date=scheduled_payment_date)

                premium = Premiums(policy_number=policy_number,
                                   scheduled_payment_date=scheduled_payment_date,
                                   payment_amount=policy_data.total_premiums)

                premium_dict = premium.dict(exclude={'late_payment_threshold_days', 'percent_charged'})
                session.add(PremiumsORM(**premium_dict))

    @error_handler
    async def send_premium_payment_notification(self,
                                                premium: Premiums,
                                                policy_data: PolicyRegistrationData):
        """

        :param policy_data:
        :param premium:
        :return:
        """
        with self.get_session() as session:

            personal_data_orm = session.query(ClientPersonalInformationORM).filter_by(uid=policy_data.uid).first()
            personal_data = ClientPersonalInformation(**personal_data_orm.to_dict())

            if personal_data.contact_id:
                contact_data_orm = session.query(ContactsORM).filter_by(contact_id=personal_data.contact_id).first()

                if isinstance(contact_data_orm, ContactsORM):
                    contact = Contacts(**contact_data_orm.to_dict())
                else:
                    return False
            else:
                return False

            company_details_orm = session.query(CompanyORM).filter_by(company_id=personal_data.company_id).first()
            branch_details_orm = session.query(CompanyBranchesORM).filter_by(branch_id=personal_data.branch_id).first()
            company_details = Company(**company_details_orm.to_dict())
            branch_details = CompanyBranches(**branch_details_orm.to_dict())

            # TODO This needs to be moved to the messaging controller
            await self.do_send_notice(personal_data=personal_data, contact=contact,
                                      policy_data=policy_data, premium=premium,
                                      company_details=company_details, branch_details=branch_details)
            return True

    @error_handler
    async def do_send_notice(self, personal_data: ClientPersonalInformation,
                             contact: Contacts,
                             policy_data: PolicyRegistrationData,
                             premium: Premiums, company_details: Company,
                             branch_details: CompanyBranches):
        """

        :param contact:
        :param personal_data:
        :param policy_data:
        :param premium:
        :param company_details:
        :param branch_details:
        :return:
        """
        context = dict(company_details=company_details, premium=premium)
        sms_template = render_template('email_templates/covers/premium_paid_sms_notice.html', **context)

        sms_message = SMSCompose(message=sms_template, to_cell=contact.cell,
                                 to_branch=personal_data.branch_id,
                                 recipient_type=RecipientTypes.CLIENTS.value)

        await self.messaging_controller.send_sms(composed_sms=sms_message)

        subject = f"Premium Payment Notification From  {company_details.company_name.capitalize()}"

        email_template = render_template('email_templates/covers/premium_paid_email_template.html', **context)
        email_message = EmailCompose(
            to_email=contact.email, subject=subject, message=email_template, to_branch=personal_data.branch_id,
            recipient_type=RecipientTypes.CLIENTS.value)

        await self.messaging_controller.send_email(email_message)

    async def create_invoice_record(self, premium: Premiums) -> PremiumReceipt:
        """

        :param premium:
        :return:
        """
        return await self.add_premium_receipt(receipt=PremiumReceipt.from_premium(premium=premium))

    @error_handler
    async def get_receipt_by_receipt_number(self, receipt_number: str) -> PremiumReceipt:
        """

        :param receipt_number:
        :return:
        """
        with self.get_session() as session:
            receipt_orm = (session.query(PremiumReceiptORM)
                           .filter_by(receipt_number=receipt_number)
                           .options(joinedload(PremiumReceiptORM.premium))
                           .first())

            return PremiumReceipt(**receipt_orm.to_dict(include_relationships=True)) if receipt_orm else None

    @error_handler
    async def get_last_receipt_by_premium_number(self, premium_id: str) -> PremiumReceipt:
        """
        :param premium_id:
        :return:
        """
        with self.get_session() as session:
            receipt_orm = (session.query(PremiumReceiptORM)
                           .filter_by(premium_id=premium_id)
                           .options(joinedload(PremiumReceiptORM.premium))
                           .first())
            return PremiumReceipt(**receipt_orm.to_dict(include_relationships=True)) if receipt_orm else None

    async def add_claim(self, claim_data: Claims) -> Claims | None:
        """

        :param claim_data:
        :return:
        """
        with self.get_session() as session:
            session.add(ClaimsORM(**claim_data.dict()))
            return claim_data
