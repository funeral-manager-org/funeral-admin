import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template
from sqlalchemy.orm import joinedload

from src.cache.cache import cached_ttl
from src.controller import Controllers, error_handler
from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.contacts import Contacts
from src.database.models.covers import ClientPersonalInformation
from src.database.models.messaging import SMSCompose, RecipientTypes, EmailCompose
from src.database.models.subscriptions import Subscriptions, PaymentNoticeInterval
from src.database.models.users import User
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM, SMSPackageORM, SubscriptionStatusORM, \
    PaymentNoticeIntervalORM


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

    @error_handler
    async def send_subscription_has_expired_notice(self, company_data: Company, subscription: Subscriptions):
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
    async def is_subscription_notice_sent_for_this_company(self, company_id: str):
        """
            ** will check if company_a has a payment notice already sent in the last three days
        :param company_id:
        :return:
        """
        with self.get_session() as session:
            notice_interval_orm = session.query(PaymentNoticeIntervalORM).filter_by(company_id=company_id).first()
            if isinstance(notice_interval_orm, PaymentNoticeIntervalORM):
                notice_interval = PaymentNoticeInterval(**notice_interval_orm.to_dict())
                return notice_interval.payment_notice_sent_within_three_days()
            return False

    @error_handler
    async def subscription_notice_sent_for_company(self, company_id: str):
        with self.get_session() as session:
            notice_interval_orm = session.query(PaymentNoticeIntervalORM).filter_by(company_id=company_id).first()
            if isinstance(notice_interval_orm, PaymentNoticeIntervalORM):
                notice_interval_orm.last_payment_notice_sent_date = datetime.today().date()

                notice_interval = PaymentNoticeInterval(**notice_interval_orm.to_dict())

    @error_handler
    async def is_expired_notice_sent_for_this_company(self, company_id: str):
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            notice_interval_orm = session.query(PaymentNoticeIntervalORM).filter_by(company_id=company_id).first()
            if isinstance(notice_interval_orm, PaymentNoticeIntervalORM):
                notice_interval = PaymentNoticeInterval(**notice_interval_orm.to_dict())
                return notice_interval.payment_expired_notice_sent_within_three_days()
            return False

    @error_handler
    async def send_notice_to_subscribe(self, company_data: Company):
        """

        :param company_data:
        :return:
        """
        self.logger.error(f"Company : {company_data.company_name} Not Subscribed")
        subject = "Funeral Manager - Subscription Not Active"
        context = dict(company_data=company_data)
        email_template = render_template('email_templates/subscription_not_active.html', **context)

        await self.send_email_to_company_admins(company_data=company_data, email_template=email_template,
                                                subject=subject)

    @error_handler
    async def send_email_to_company_admins(self, company_data, email_template, subject):
        company_accounts: list[User] = await self.user_controller.get_company_accounts(
            company_id=company_data.company_id)
        for account in company_accounts:
            if account.is_company_admin and account.account_verified:
                recipient_type = RecipientTypes.EMPLOYEES.value
                await self.messaging_controller.send_email(email=EmailCompose(to_email=account.email,
                                                                              subject=subject,
                                                                              message=email_template,
                                                                              to_branch=account.branch_id,
                                                                              recipient_type=recipient_type))

    @error_handler
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

    @error_handler
    async def add_package_to_subscription(self, subscription: Subscriptions, company_id: str):
        """

        :return:
        """
        with self.get_session() as session:
            sms_packages_orm_list = session.query(SMSPackageORM).filter_by(company_id=company_id).all()

            for package in sms_packages_orm_list:
                subscription.total_sms += package.use_package()

            return subscription

    @error_handler
    async def do_send_upcoming_payment_reminders(self, company_data: Company):
        """
        Send upcoming payment reminders to clients.

        :param company_data:
        :return: None
        """

        subscription_orm: SubscriptionsORM = await self.get_subscription_orm(company_id=company_data.company_id)
        if subscription_orm:
            subscription = Subscriptions(**subscription_orm.to_dict())
        else:
            self.logger.error(f"Company Not Subscribed: {company_data.company_name}")

            notice_to_subscribe_sent_recently = await self.is_subscription_notice_sent_for_this_company(
                company_id=company_data.company_id)

            if not notice_to_subscribe_sent_recently:
                # will only send notice to subscribe in cases where the notice has not been sent recently
                await self.send_notice_to_subscribe(company_data=company_data)

                # indicate that for this company subscription notice has already been sent
                await self.subscription_notice_sent_for_company(company_id=company_data.company_id)

            return False

        if subscription.is_expired() or (not subscription.is_paid_for_current_month):

            subscription_expired_notice_already_sent = await self.is_expired_notice_sent_for_this_company(
                company_id=company_data.company_id)

            if not subscription_expired_notice_already_sent:
                # send subscription has expired notice if it has not been sent recently
                await self.send_subscription_has_expired_notice(company_data=company_data, subscription=subscription)

            return False

        # Retrieve policy holders for the company
        policy_holders = await self.company_controller.get_policy_holders(company_id=company_data.company_id)

        # Add a package to the subscription if needed
        subscription = await self.add_package_to_subscription(subscription=subscription,
                                                              company_id=company_data.company_id)

        for holder in policy_holders:
            if holder.contact_id:
                is_sent = await self.send_payment_reminder(holder, subscription, company_data)
                if not is_sent:
                    break

        await self.update_subscription(subscription=subscription)
        return True

    @error_handler
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
            return True
        else:
            await self.handle_insufficient_sms_credit(company_data=company_data)
            return False

    @error_handler
    async def get_subscription_orm(self, company_id: str):
        """
        Retrieve subscription ORM for a company, including related payments.

        :param company_id: The ID of the company.
        :return: SubscriptionORM
        """
        with self.get_session() as session:
            return session.query(SubscriptionsORM) \
                .options(joinedload(SubscriptionsORM.payments)) \
                .filter_by(company_id=company_id) \
                .first()

    @error_handler
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

    @error_handler
    async def handle_insufficient_sms_credit(self, company_data: Company):
        """
        **handle_insufficient_sms_credit**
            Handle insufficient SMS credit scenario.

            :return: None
        """
        company_accounts: list[User] = await self.user_controller.get_company_accounts(
            company_id=company_data.company_id)
        subject = "Funeral Manager - SMS Credit Exhausted"
        for account in company_accounts:
            if account.is_company_admin and account.account_verified:
                template = await self.create_email_template(account=account)
                email = EmailCompose(to_email=account.email, subject=subject, message=template,
                                     to_branch=account.branch_id, recipient_type=RecipientTypes.EMPLOYEES.value)

                await self.messaging_controller.send_email(email=email)

    @error_handler
    async def do_send_lapsed_policy_notifications(self, company_data: Company):
        """

        :param company_data:
        :return:
        """
        subscription_orm: SubscriptionsORM = await self.get_subscription_orm(company_id=company_data.company_id)
        if not subscription_orm:
            await self.send_notice_to_subscribe(company_data=company_data)
            return False

        subscription = Subscriptions(**subscription_orm.to_dict())
        insufficient_credit = False

        if subscription.is_expired() or (not subscription.is_paid_for_current_month):
            await self.send_subscription_has_expired_notice(company_data=company_data, subscription=subscription)
            return False

        branches_list = await self.company_controller.get_company_branches(company_id=company_data.company_id)

        for branch in branches_list:
            branch_contact = await self.company_controller.get_contact(contact_id=branch.contact_id)
            policy_holders = await self.company_controller.get_branch_policy_holders_with_lapsed_policies(
                branch_id=branch.branch_id)
            for policy_holder in policy_holders:
                if policy_holder.contact_id:
                    contact_detail = await self.company_controller.get_contact(contact_id=policy_holder.contact_id)
                    if contact_detail and contact_detail.cell:
                        sms = f"""
                        Company Name: {company_data.company_name}
                        
                        We would like to inform you that your funeral policy
                        with policy number : {policy_holder.policy_number} , has lapsed
                        please make payment as soon as possible to avoid problems.
                        
                        for arrangements please contact us at  Cell : {branch_contact.cell}
                        
                        Thank You 
                        {company_data.company_name}
                        {branch_contact.cell}                        
                        """
                        if subscription.take_sms_credit():
                            sms = self.create_sms_message(message=sms, contact_data=contact_detail,
                                                          branch_id=branch.branch_id)
                            await self.messaging_controller.send_sms(composed_sms=sms)

                        else:
                            insufficient_credit = True
                            break
            # Update Subscription so that the credit used is subtracted
            await self.update_subscription(subscription=subscription)

            if insufficient_credit:
                await self.handle_insufficient_sms_credit(company_data=company_data)
                break
        return True

    @error_handler
    async def execute_reminders(self):
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
            self.logger.info(f"SMS Settings : {sms_settings}")
            if sms_settings and sms_settings.enable_sms_notifications:
                is_ok = False
                #     Payment Notifications Reminders
                if sms_settings.upcoming_payments_notifications:
                    self.logger.info(f"Reminders Ok to send for Company : {company.company_name}")
                    is_ok = await self.do_send_upcoming_payment_reminders(company_data=company)

                #  is_ok prevents lapsed notifications from running if payment reminders did not succeed Lapsed Policy Reminders
                if is_ok and sms_settings.policy_lapsed_notifications:
                    self.logger.info(
                        f"Will Attempt sending Policy Lapsed Notifications for Company: {company.company_name}")
                    await self.do_send_lapsed_policy_notifications(company_data=company)

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
            try:
                await self.execute_reminders()
            except Exception:
                await asyncio.sleep(sleep_duration * 100)

            # Sleep until the next execution time
            await asyncio.sleep(sleep_duration)
