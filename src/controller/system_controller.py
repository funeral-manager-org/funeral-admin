from flask import Flask

from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.companies import Company
from src.database.models.subscriptions import Subscriptions
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM


class SystemController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    @error_handler
    async def get_all_companies(self) -> list[Company]:
        """
            will return a list of all companies registered on the system
        :return:
        """
        with self.get_session() as session:
            companies_orm_list = session.query(CompanyORM).all()
            return [Company(**company_orm.to_dict()) for company_orm in companies_orm_list if
                    isinstance(company_orm, CompanyORM)]

    @error_handler
    async def get_subscriptions(self, company_id: str) -> list[Subscriptions]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            subscriptions_orm_list = session.query(SubscriptionsORM).all()
            return [Subscriptions(**sub_orm.to_dict()) for sub_orm in subscriptions_orm_list]

    @error_handler
    async def get_subscription(self, subscription_id: str) -> Subscriptions | None:
        """

        :param subscription_id:
        :return:
        """
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter_by(subscription_id=subscription_id).first()
            if isinstance(subscription_orm, SubscriptionsORM):
                return Subscriptions(**subscription_orm.to_dict())
            return None