import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template

from src.controller import Controllers, error_handler
from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.contacts import Contacts
from src.database.models.covers import ClientPersonalInformation
from src.database.models.messaging import SMSCompose, RecipientTypes, EmailCompose
from src.database.models.subscriptions import Subscriptions
from src.database.models.users import User
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM, SMSPackageORM


class SubscriptionsController(Controllers):
    """

    """

    def __init__(self):
        pass

    def init_app(self, app: Flask):
        pass

    async def add_company_subscription(self, subscription: Subscriptions) -> Subscriptions:
        """
            this will add company subscription record to database
        :param subscription:
        :return:
        """
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter_by(company_id=subscription.company_id).first()
            if isinstance(subscription_orm, SubscriptionsORM):
                this_subscription_ = Subscriptions(**subscription_orm.to_dict())
                if this_subscription_.is_expired():
                    subscription_orm.plan_name = subscription.plan_name
                    subscription_orm.total_sms = subscription.total_sms
                    subscription_orm.total_emails = subscription.total_emails
                    subscription_orm.total_clients = subscription.total_clients
                    subscription_orm.date_subscribed = subscription.date_subscribed
                    subscription_orm.subscription_amount = subscription.subscription_amount
                    subscription_orm.subscription_period = subscription.subscription_period

                elif this_subscription_.plan_name == subscription.plan_name:
                    this_subscription_.subscription_period += subscription.subscription_period
                    subscription_orm.subscription_period = this_subscription_.subscription_period

                else:
                    subscription_orm.plan_name = subscription.plan_name
                    subscription_orm.total_sms = subscription.total_sms
                    subscription_orm.total_emails = subscription.total_emails
                    subscription_orm.total_clients = subscription.total_clients
                    subscription_orm.date_subscribed = subscription.date_subscribed
                    subscription_orm.subscription_amount = subscription.subscription_amount
                    subscription_orm.subscription_period = subscription.subscription_period

                    subscription_orm.total_sms += this_subscription_.total_sms
                    subscription_orm.total_emails += this_subscription_.total_emails
                subscription = Subscriptions(**subscription_orm.to_dict())
            else:
                new_subscription_orm = SubscriptionsORM(**subscription.dict())
                session.add(new_subscription_orm)

            session.commit()
            return subscription
