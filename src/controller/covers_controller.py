from flask import Flask

from src.database.sql.covers import PremiumsORM
from src.database.models.covers import Premiums
from src.controller import Controllers


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

    async def add_premiums_payment(self, premium_payment: Premiums) -> Premiums:
        """

        :param premium_payment:
        :return:
        """
        with self.get_session() as session:
            payment_orm = PremiumsORM(**premium_payment.dict())
            session.add(payment_orm)

            return premium_payment
