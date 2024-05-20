import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template

from database.models.users import User
from emailer import EmailModel
from main import send_mail
from src.controller import Controllers, error_handler
from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.contacts import Contacts
from src.database.models.covers import ClientPersonalInformation
from src.database.models.messaging import SMSCompose, RecipientTypes
from src.database.models.subscriptions import Subscriptions
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM, SMSPackageORM


class SubscriptionExpiredException(Exception):
    """Exception raised when a subscription is expired."""

    def __init__(self, message="Subscription is expired."):
        self.message = message
        super().__init__(self.message)


class NotificationsController(Controllers):

    def __init__(self):
        super().__init__()
        self.messaging_controller: MessagingController | None = None
        self.company_controller: CompanyController | None = None
        self.user_controller: UserController | None = None
        self.loop = asyncio.get_event_loop()

    @staticmethod
    async def template_message(company_data, date_str, day_name, holder, policy_registration_data):
        """
            template message for payment reminder
        :param company_data:
        :param date_str:
        :param day_name:
        :param holder:
        :param policy_registration_data:
        :return:
        """
        _message = f"""
                                {company_data.company_name}

                                Premium Payment Reminder
                                Hello {holder.full_names} {holder.surname}

                                This is to remind you that your next premium payment date will be on 

                                {day_name} {date_str}

                                Please be sure to make payment on or before this date.

                                Next Premium Amount : R {policy_registration_data.total_premiums}.00

                                Thank You. 
                                """
        return _message

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, messaging_controller: MessagingController, company_controller: CompanyController,
                 user_controller: UserController):
        """
        **init_app**

            :param user_controller:
            :param company_controller:
            :param messaging_controller:
            :param app:
            :return:
        """
        super().init_app(app=app)
        self.messaging_controller = messaging_controller
        self.company_controller = company_controller
        self.user_controller = user_controller
        self.loop.create_task(self.daemon_runner())

    async def update_subscription(self, subscription: Subscriptions):
        """

        :param subscription:
        :return:
        """
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter_by(company_id=subscription.company_id).first()
            if isinstance(subscription_orm, SubscriptionsORM):
                subscription_orm.plan_name = subscription.plan_name
                subscription_orm.total_sms = subscription.total_sms
                subscription_orm.total_emails = subscription.total_emails
                subscription_orm.total_clients = subscription.total_clients
                subscription_orm.date_subscribed = subscription.date_subscribed
                subscription_orm.subscription_amount = subscription.subscription_amount
                subscription_orm.subscription_period = subscription.subscription_period

                session.commit()
        pass

    async def add_package_to_subscription(self, subscription: Subscriptions, company_id: str):
        """

        :return:
        """
        with self.get_session() as session:
            sms_packages_orm_list = session.query(SMSPackageORM).filter_by(company_id=company_id).all()

            for package in sms_packages_orm_list:
                subscription.total_sms += package.use_package()
            session.commit()
            return subscription

    async def do_send_upcoming_payment_reminders(self, company_id: str):
        """
        Send upcoming payment reminders to clients.

        :param company_id: The ID of the company.
        :return: None
        """
        try:
            # Retrieve company details and subscription information
            company_data: Company = await self.company_controller.get_company_details(company_id=company_id)
            subscription_orm: SubscriptionsORM = await self.get_subscription_orm(company_id)
            subscription = Subscriptions(**subscription_orm.to_dict())

            if subscription.is_expired():
                raise SubscriptionExpiredException("Subscription is expired.")

            # Retrieve policy holders for the company
            policy_holders = await self.company_controller.get_policy_holders(company_id=company_id)

            # Add a package to the subscription if needed
            subscription = await self.add_package_to_subscription(subscription=subscription, company_id=company_id)

            for holder in policy_holders:
                if holder.contact_id:
                    await self.send_payment_reminder(holder, subscription, company_data)

            await self.update_subscription(subscription=subscription)
        except Exception as e:
            self.logger.error(f"Error in sending payment reminders: {str(e)}")

    async def send_payment_reminder(self, holder: ClientPersonalInformation, subscription: Subscriptions,
                                    company_data: Company):
        """
        Send a payment reminder to a client.

        :param holder: The policy holder.
        :param subscription: The subscription.
        :param company_data: The company data.
        :return: None
        """
        policy_registration_data = await self.company_controller.get_policy_with_policy_number(
            policy_number=holder.policy_number)
        contact_data = await self.company_controller.get_contact(contact_id=holder.contact_id)

        if not (policy_registration_data.can_send_payment_reminder() and contact_data.cell):
            return

        if subscription.take_sms_credit():
            message = await self.construct_message(company_data=company_data,
                                                   holder=holder,
                                                   policy_registration_data=policy_registration_data)

            sms_message = self.create_sms_message(message=message,
                                                  contact_data=contact_data,
                                                  branch_id=holder.branch_id)

            await self.messaging_controller.send_sms(composed_sms=sms_message)
            self.logger.info("Sent payment reminder: {}".format(message))
        else:
            await self.handle_insufficient_sms_credit(company_data=company_data)

    @error_handler
    async def get_subscription_orm(self, company_id: str):
        """
        Retrieve subscription ORM for a company.

        :param company_id: The ID of the company.
        :return: SubscriptionORM
        """
        with self.get_session() as session:
            return session.query(SubscriptionsORM).filter_by(company_id=company_id).first()

    async def construct_message(self, company_data, holder, policy_registration_data):
        """
        Construct the message for the payment reminder.

        :param company_data: The company data.
        :param holder: The policy holder.
        :param policy_registration_data: The policy registration data.
        :return: str
        """
        day_name, date_str = policy_registration_data.return_next_payment_date()
        return await self.template_message(company_data, date_str, day_name, holder, policy_registration_data)

    @staticmethod
    def create_sms_message(message: str, contact_data: Contacts, branch_id: str):
        """
        Create an SMS message.

        :param message: The message content.
        :param contact_data: The contact data.
        :param branch_id: The branch ID.
        :return: SMSCompose
        """
        return SMSCompose(
            message=message,
            to_cell=contact_data.cell,
            to_branch=branch_id,
            recipient_type=RecipientTypes.CLIENTS.value
        )

    async def create_email_template(self, account: User) -> str:
        """
        Will recreate an email template
        :param account:
        :return:
        """
        employee_record = await self.company_controller.get_employee_by_uid(uid=account.uid)
        return render_template('email_templates/sms_credits_exhausted.html',
                               employee_record=employee_record)

    async def handle_insufficient_sms_credit(self, company_data: Company):
        """
        **handle_insufficient_sms_credit**
            Handle insufficient SMS credit scenario.

            :return: None
        """
        company_accounts: list[User] = await self.user_controller.get_company_accounts(
            company_id=company_data.company_id)
        for account in company_accounts:
            if account.is_company_admin and account.account_verified:
                template = await self.create_email_template(account=account)
                email = EmailModel(to_=account.email, subject_="Funeral Manager - SMS Credit Exhausted", html_=template)
                send_mail.send_mail_resend(email=email)

    async def execute_payment_reminders(self):
        """
            This Method will go through all the covers and all clients
            then send payment reminders to every client
        :return:
        """
        with self.get_session() as session:
            companies_orm_list = session.query(CompanyORM).all()
            companies_list = [Company(**company_orm.to_dict()) for company_orm in companies_orm_list]

        for company in companies_list:
            sms_settings = await self.messaging_controller.sms_service.get_sms_settings(company_id=company.company_id)
            self.logger.info(f"Payment Reminders for Company : {company.company_name}")
            if sms_settings and sms_settings.enable_sms_notifications and sms_settings.upcoming_payments_notifications:
                self.logger.info(f"Reminders Ok to send for Company : {company.company_name}")
                await self.do_send_upcoming_payment_reminders(company_id=company.company_id)

    async def daemon_runner(self):
        """
        Daemon runner that checks if it's time to execute send_payment_reminders,
        sleeps until the next execution time, and then executes the reminders.

        :return: None
        """
        self.logger.info("Started Notifications Daemon")

        while True:
            # Get the current time
            now = datetime.now()

            # Calculate the time until the next execution time (e.g., 9:00 AM)
            next_execution_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now >= next_execution_time:
                next_execution_time += timedelta(days=1)  # Move to the next day if already past execution time
            sleep_duration = (next_execution_time - now).total_seconds()

            # Schedule the payment reminders task to run at the next execution time
            await self.execute_payment_reminders()

            # Sleep until the next execution time
            await asyncio.sleep(sleep_duration)
