import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template
from sqlalchemy.orm import joinedload

from src.database.sql.companies import CompanyBranchesORM
from src.database.sql.user import UserORM
from src.controller import Controllers, error_handler
from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.messaging import RecipientTypes, EmailCompose
from src.database.models.payments import Payment
from src.database.models.subscriptions import Subscriptions, SubscriptionStatus, TopUpPacks, Package
from src.database.models.users import User
from src.database.sql.subscriptions import SubscriptionsORM, PaymentORM, SubscriptionStatusORM, PackageORM


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

    async def add_update_sms_email_package(self, top_up_pack: TopUpPacks) -> TopUpPacks:
        """

        :param top_up_pack:
        :return:
        """
        with self.get_session() as session:

            package = Package(company_id=top_up_pack.company_id, package_name=top_up_pack.top_up_name,
                              total_sms=top_up_pack.total_sms, total_email=top_up_pack.total_emails, is_paid=False)

            package_orm = PackageORM(**package.dict())
            session.add(package_orm)

            return top_up_pack

    async def set_package_to_paid(self, package_id: str):
        """

        :param package_id:
        :return:
        """
        with self.get_session() as session:
            package_orm: PackageORM = session.query(PackageORM).filter_by(package_id=package_id).first()
            if isinstance(package_orm, PackageORM) and package_orm.total_sms > 0:
                package_orm.is_paid = True

            return isinstance(package_orm, PackageORM)

    async def remove_package_its_unpaid(self, package_id: str):
        with self.get_session() as session:
            package_orm = session.query(PackageORM).filter_by(package_id=package_id).first()
            if isinstance(package_orm, PackageORM) and not package_orm.is_paid:
                session.delete(package_orm)
            else:
                pass
                #   TODO check if its an email package

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
                    subscription_orm.date_subscribed = subscription.subscribed_date
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
                    subscription_orm.date_subscribed = subscription.subscribed_date
                    subscription_orm.subscription_amount = subscription.subscription_amount
                    subscription_orm.subscription_period = subscription.subscription_period

                    subscription_orm.total_sms += this_subscription_.total_sms
                    subscription_orm.total_emails += this_subscription_.total_emails
                subscription = Subscriptions(**subscription_orm.to_dict())
            else:
                new_subscription_orm = SubscriptionsORM(**subscription.dict())
                session.add(new_subscription_orm)

        return subscription

    @error_handler
    async def add_company_payment(self, payment: Payment):
        """

        :param payment:
        :return:
        """
        with self.get_session() as session:
            session.add(PaymentORM(**payment.dict()))
            session.commit(payment)

            return payment

    @error_handler
    async def updated_branch_details(self, account: User) -> User:
        with self.get_session() as session:
            account_orm = session.query(UserORM).filter_by(uid=account.uid).first()
            branch_orm = session.query(CompanyBranchesORM).filter_by(company_id=account.company_id).first()
            if isinstance(branch_orm, CompanyBranchesORM):
                account_orm.branch_id = branch_orm.to_dict().get('branch_id')

            return User(**account_orm.to_dict())
    @error_handler
    async def send_email_to_company_admins(self, company_data, email_template, subject):
        company_accounts: list[User] = await self.user_controller.get_company_accounts(
            company_id=company_data.company_id)
        for account in company_accounts:
            if account.is_company_admin and account.account_verified:
                if not account.branch_id:
                    account = await self.updated_branch_details(account=account)
                await self.messaging_controller.send_email(email=EmailCompose(to_email=account.email,
                                                                              subject=subject,
                                                                              message=email_template,
                                                                              to_branch=account.branch_id,
                                                                              recipient_type=RecipientTypes.EMPLOYEES.value))

    @error_handler
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

    @error_handler
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
            subscriptions_orm_list = session.query(SubscriptionsORM).options(
                joinedload(SubscriptionsORM.payments)).all()
            subscriptions_list = [Subscriptions(**sub_orm.to_dict()) for sub_orm in subscriptions_orm_list]

            return subscriptions_list

    @error_handler
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
        un_paid_subscriptions = [sub for sub in subscriptions if not sub.is_paid_for_current_month]

        await self.notify_managers_to_pay_their_subscriptions(un_paid_subs=un_paid_subscriptions)

    @error_handler
    async def remove_old_unpaid_subscriptions(self):
        """
        Removes unpaid subscriptions older than 30 days
        """
        subscriptions = await self.get_subscriptions()
        self.logger.info(f"Checking for Unpaid Subscriptions: {subscriptions}")
        un_paid_subscriptions: list[Subscriptions] = [sub for sub in subscriptions if not sub.is_paid_for_current_month]

        thirty_days_ago = datetime.now() - timedelta(days=30)

        for subscription in un_paid_subscriptions:
            if subscription.subscribed_date < thirty_days_ago:
                await self.remove_subscription(subscription)
                self.logger.info(f"Removed unpaid subscription: {subscription}")

    @error_handler
    async def remove_subscription(self, subscription):
        # Placeholder for the actual removal logic
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter_by(
                subscription_id=subscription.subscription_id).first()
            if subscription_orm:
                session.delete(subscription_orm)

    @error_handler
    async def get_company_subscription(self, company_id: str) -> Subscriptions | None:
        with self.get_session() as session:
            subscription_orm = (session.query(SubscriptionsORM)
                                .options(joinedload(SubscriptionsORM.payments))
                                .filter_by(company_id=company_id).first())

            if not subscription_orm:
                return None

            return Subscriptions(**subscription_orm.to_dict())

    @error_handler
    async def check_and_set_subscription_status(self) -> bool:
        """
        will return true if subscription status has not been checked this week
        :return:
        """
        with self.get_session() as session:
            subscription_status_orm = session.query(SubscriptionStatusORM).first()
            if isinstance(subscription_status_orm, SubscriptionStatusORM):
                subscription_status = SubscriptionStatus(**subscription_status_orm.to_dict())
                return subscription_status.subscription_checked_recently()
            else:
                subscription_status = SubscriptionStatus()
                session.add(SubscriptionStatusORM(**subscription_status.dict()))

            return False

    @error_handler
    async def set_subscription_checked_status(self):
        """

            will set that subscription status has been checked for this week
        :return:
        """
        with self.get_session() as session:
            subscription_status_orm = session.query(SubscriptionStatusORM).first()
            if isinstance(subscription_status_orm, SubscriptionStatusORM):
                subscription_status_orm.last_checked = datetime.today().date()
            else:
                subscription_status = SubscriptionStatus()
                session.add(SubscriptionStatusORM(**subscription_status.dict()))

    async def daemon_util(self):
        """
            **daemon_util**
            runs continuously to check if subscriptions are paid

        :return:
        """
        twelve_hours = 60 * 60 * 12
        while True:
            self.logger.info("Subscriptions Daemon started")

            await self.remove_old_unpaid_subscriptions()
            # this checks if subscription status has been checked for this week
            is_checked_this_week = await self.check_and_set_subscription_status()
            if not is_checked_this_week:
                # this sets the status that everything was checked this week
                await self.set_subscription_checked_status()
                # this check will run once a week
                await self.check_if_subscriptions_are_paid()
            else:
                self.logger.info("We Already checked subscription status this week and sent notifications")

            await asyncio.sleep(delay=twelve_hours)
