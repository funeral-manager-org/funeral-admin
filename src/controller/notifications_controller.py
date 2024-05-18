import asyncio
from datetime import datetime, timedelta

from flask import Flask

from src.database.models.contacts import Contacts
from src.database.models.messaging import SMSCompose, RecipientTypes
from src.controller import Controllers
from src.controller.company_controller import CompanyController
from src.controller.messaging_controller import MessagingController
from src.database.models.companies import Company
from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation
from src.database.models.subscriptions import Subscriptions
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM, SMSPackageORM


class NotificationsController(Controllers):

    def __init__(self):
        super().__init__()
        self.messaging_controller: MessagingController | None = None
        self.company_controller: CompanyController | None = None
        self.loop = asyncio.get_event_loop()

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, messaging_controller: MessagingController, company_controller: CompanyController):
        """
        **init_app**

            :param company_controller:
            :param messaging_controller:
            :param app:
            :return:
        """
        super().init_app(app=app)
        self.messaging_controller = messaging_controller
        self.company_controller = company_controller
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
            TODO -
                check if there is enough sms credits
                open the cover record and get client details
                send sms reminder

        :param company_id:
        :return:
        """
        with self.get_session() as session:

            company_data = await self.company_controller.get_company_details(company_id=company_id)
            subscription_orm = session.query(SubscriptionsORM).filter_by(company_id=company_id).first()

            subscription = Subscriptions(**subscription_orm.to_dict())

            if not subscription.is_expired():
                policy_holders: list[ClientPersonalInformation] = await self.company_controller.get_policy_holders(
                    company_id=company_id)
                subscription: Subscriptions = await self.add_package_to_subscription(subscription=subscription,
                                                                                     company_id=company_id)
                for holder in policy_holders:
                    if holder.contact_id:
                        policy_registration_data: PolicyRegistrationData = await self.company_controller.get_policy_with_policy_number(
                            policy_number=holder.policy_number)

                        contact_data: Contacts = await self.company_controller.get_contact(
                            contact_id=holder.contact_id)

                        if policy_registration_data.can_send_payment_reminder() and contact_data.cell:
                            # send SMS Notification
                            day_name, date_str = policy_registration_data.return_next_payment_date()
                            if subscription.take_sms_credit():
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
                                sms_message: SMSCompose = SMSCompose(message=_message,
                                                                     to_cell=contact_data.cell,
                                                                     to_branch=holder.branch_id,
                                                                     recipient_type=RecipientTypes.CLIENTS.value)

                                await self.messaging_controller.send_sms(composed_sms=sms_message)
                                log_message = f"""
                                    Sent a Payment Reminder to 
                                        Client : {holder.full_names} {holder.surname}  
                                        Cell: {contact_data.cell}
                                        """
                                self.logger.info(log_message)
                            else:
                                pass
                                # TODO - send notification to company manager that the SMS credit has been used up

                    await self.update_subscription(subscription=subscription)

                else:
                    pass
                    #   TODO - send a notification to company_manager that the subscription has expired

    async def send_payment_reminders(self):
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
            sms_settings = await self.messaging_controller.sms_service.get_sms_settings(company_id=company.company_id)
            self.logger.info(f"Payment Reminders for Company : {company.company_name}")
            if sms_settings and sms_settings.enable_sms_notifications and sms_settings.upcoming_payments_notifications:
                self.logger.info(f"Reminders Ok to send for Company : {company.company_name}")
                await self.do_send_upcoming_payment_reminders(company_id=company.company_id)

    async def daemon_runner(self):
        """
        Daemon runner that checks if the day has changed,
        sleeps until the next midnight, and then executes send_payment_reminders.

        :return: None
        """
        one_hour = 1 * 60 * 60
        last_day = datetime.today().date()
        self.logger.info("started Notifications Daemon")

        while True:
            current_day = datetime.today().date()
            self.logger.info(f"Current Day : {current_day}")

            if current_day != last_day:
                last_day = current_day
                self.logger.info(f"Executing payment reminders on {last_day}")
                await self.send_payment_reminders()

                # Calculate the time to sleep until the next midnight
                now = datetime.now()
                next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_duration = (next_midnight - now).total_seconds()
                await asyncio.sleep(sleep_duration)
            else:
                # Sleep for a short duration if it's still the same day
                await asyncio.sleep(one_hour)  # Sleep for 1 hour
