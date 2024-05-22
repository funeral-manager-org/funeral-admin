import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template

from src.controller import Controllers, error_handler
from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.messaging import RecipientTypes, EmailCompose
from src.database.models.payments import Payment
from src.database.models.subscriptions import Subscriptions
from src.database.models.users import User
from src.database.sql.subscriptions import SubscriptionsORM, PaymentORM


class SubscriptionsController(Controllers):
    """

    """

    def __init__(self):
        super().__init__()
        self.company_controller: CompanyController | None = None
        self.messaging_controller: MessagingController | None = None
        self.user_controller: UserController | None = None
        self.loop = asyncio.get_event_loop()

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask,
                 company_controller: CompanyController,
                 messaging_controller: MessagingController,
                 user_controller: UserController):
        super().init_app(app=app)
        self.company_controller = company_controller
        self.messaging_controller = messaging_controller
        self.user_controller = user_controller
        self.loop.create_task(self.daemon_util())
        pass

    @error_handler
    async def add_update_company_subscription(self, subscription: Subscriptions) -> Subscriptions:
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

    async def add_company_payment(self, payment: Payment):
        """

        :param payment:
        :return:
        """
        with self.get_session() as session:
            session.add(PaymentORM(**payment.dict()))
            session.commit(payment)
            return payment

    # noinspection DuplicatedCode
    async def send_email_to_company_admins(self, company_data, email_template, subject):
        company_accounts: list[User] = await self.user_controller.get_company_accounts(
            company_id=company_data.company_id)
        for account in company_accounts:
            if account.is_company_admin and account.account_verified:
                await self.messaging_controller.send_email(email=EmailCompose(to_email=account.email,
                                                                              subject=subject,
                                                                              message=email_template,
                                                                              to_branch=account.branch_id,
                                                                              recipient_type=RecipientTypes.EMPLOYEES.value))

    async def subscription_has_expired(self, company_data: Company, subscription: Subscriptions):
        """

        :param subscription:
        :param company_data:
        :return:
        """
        self.logger.error(
            f"Subscription for company : {company_data.company_name} ID: {company_data.company_id} Has Expired")

        subject = "Funeral Manager - Subscription Expired"
        context = dict(subscription=subscription, company_data=company_data)
        email_template = render_template('email_templates/subscription_expired.html', **context)

        await self.send_email_to_company_admins(company_data=company_data, email_template=email_template,
                                                subject=subject)

    async def notify_managers_to_pay_their_subscriptions(self, un_paid_subs: list[Subscriptions]):
        """

        :param un_paid_subs:
        :return:
        """
        for subscription in un_paid_subs:
            company_data = await self.company_controller.get_company_details(company_id=subscription.company_id)
            await self.subscription_has_expired(company_data=company_data, subscription=subscription)

    @error_handler
    async def get_subscriptions(self) -> list[Subscriptions]:
        """
        :return:
        """
        with self.get_session() as session:
            subscriptions_orm_list = session.query(SubscriptionsORM).all()
            return [Subscriptions(**sub_orm.to_dict()) for sub_orm in subscriptions_orm_list]

    async def check_if_subscriptions_are_paid(self):
        """
        **check_if_subscriptions_are_paid*8
        this method looks up upaid subscriptions and then once it finds them it notifies the company admin
        of this so payment can be made
            should check if
        :return:
        """
        subscriptions = await self.get_subscriptions()
        self.logger.info(f"Checking for Unpaid Subscription : {subscriptions}")
        un_paid_subscriptions = [sub for sub in subscriptions if not sub.is_paid_for_current_month()]

        await self.notify_managers_to_pay_their_subscriptions(un_paid_subs=un_paid_subscriptions)

    async def remove_old_unpaid_subscriptions(self):
        """
        Removes unpaid subscriptions older than 30 days
        """
        subscriptions = await self.get_subscriptions()
        self.logger.info(f"Checking for Unpaid Subscriptions: {subscriptions}")
        un_paid_subscriptions: list[Subscriptions] = [sub for sub in subscriptions if not sub.is_paid_for_current_month()]

        thirty_days_ago = datetime.now() - timedelta(days=30)

        for subscription in un_paid_subscriptions:
            if subscription.subscribed_date < thirty_days_ago:
                await self.remove_subscription(subscription)
                self.logger.info(f"Removed unpaid subscription: {subscription}")

    async def remove_subscription(self, subscription):
        # Placeholder for the actual removal logic
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter_by(subscription_id=subscription.subscription_id).first()
            if subscription_orm:
                session.delete(subscription_orm)
                session.commit()

    async def daemon_util(self):
        """
            **daemon_util**
            runs continuously to check if subscriptions are paid

        :return:
        """

        twelve_hours = 60 * 60 * 12

        while True:
            self.logger.info("Subscriptions Daemon started")
            try:
                await self.remove_old_unpaid_subscriptions()
                await self.check_if_subscriptions_are_paid()
            except Exception as e:
                self.logger.error(f"Error : {str(e)}")

            await asyncio.sleep(delay=twelve_hours)
