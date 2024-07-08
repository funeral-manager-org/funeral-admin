import datetime
from datetime import date

from dateutil.relativedelta import relativedelta
from flask import Flask
from sqlalchemy.orm import joinedload

from src.controller import Controllers, error_handler
from src.database.models.covers import Premiums, PremiumInvoice, PolicyRegistrationData
from src.database.sql.covers import PremiumsORM, PolicyRegistrationDataORM


def next_due_date(start_date: date) -> date:
    """
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

    def init_app(self, app: Flask):
        """
            pass
        :param app:
        :return:
        """
        super().init_app(app=app)

    @error_handler
    async def add_update_premiums_payment(self, premium_payment: Premiums) -> Premiums:
        """

        :param premium_payment:
        :return:
        """
        with self.get_session() as session:
            premium_orm = session.query(PremiumsORM).filter_by(premium_id=premium_payment.premium_id).first()
            if isinstance(premium_orm, PremiumsORM):
                premium_orm.amount_paid = premium_payment.amount_paid
                premium_orm.date_paid = premium_payment.date_paid
                premium_orm.payment_method = premium_payment.payment_method
                premium_orm.payment_status = premium_payment.payment_status
                premium_orm.next_payment_amount = premium_payment.next_payment_amount
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
    async def add_premium_invoice(self, invoice: PremiumInvoice, premium_id: str):
        with self.get_session() as session:
            pass

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

    async def create_forecasted_premiums(self, policy_number: str, total: int = 12):
        """

        :return:
        """
        policy_data: PolicyRegistrationData = await self.get_policy_data(policy_number=policy_number)

        with self.get_session() as session:
            today = datetime.datetime.now().date()
            scheduled_payment_date = policy_data.next_payment_date()

            for i in range(1, total, 1):
                scheduled_payment_date = next_due_date(start_date=scheduled_payment_date)
                premium = Premiums(policy_number=policy_number, scheduled_payment_date=scheduled_payment_date,
                                   payment_amount=policy_data.total_premiums)

                premium_dict = premium.dict(exclude={'late_payment_threshold_days', 'percent_charged'})
                session.add(PremiumsORM(**premium_dict))

