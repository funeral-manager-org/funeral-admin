import asyncio
import time
from datetime import datetime

import requests
from flask import Flask

from twilio.rest import Client
from src.config import Settings
from src.controller import Controllers
from src.database.models.messaging import SMSInbox, EmailCompose, SMSCompose, SMSSettings
from src.database.sql.messaging import SMSInboxORM, SMSComposeORM, EmailComposeORM, SMSSettingsORM
from src.emailer import EmailModel, SendMail
from src.utils import create_id


def date_time() -> str:
    """"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class EmailService(Controllers):

    def __init__(self):
        super().__init__()
        self.cool_down_on_error = 20
        self.from_ = None
        self.email_sender = None
        self.sent_email_queue: dict[str, EmailModel] = {}

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, settings: Settings, emailer: SendMail = None):
        """"""
        super().init_app(app=app)
        self.email_sender = emailer
        self.from_ = settings.EMAIL_SETTINGS.RESEND.from_

    async def send_email(self, email: EmailCompose):
        """
            Email Will be Sent to Resend.com API
        :param email:
        :return:
        """
        try:
            response, email_ = await self.email_sender.send_mail_resend(email=email)

            self.logger.info(f"Sent Email Response : {response}")

            self.sent_email_queue[response.get('id', create_id())] = email_

            # Saving Sent Message to the Database
            with self.get_session() as session:
                sent_email_orm = EmailComposeORM(**email_.dict())
                session.add(sent_email_orm)
                session.commit()

        except requests.exceptions.ConnectTimeout:
            self.logger.error("Resend Connection TimeOut")
            await asyncio.sleep(delay=self.cool_down_on_error)
            await self.send_email(email=email)

    async def receive_email(self, sender: str, subject: str, body: str):
        # Code to receive email from email service API
        self.logger.info(f"Received email from {sender} with subject: {subject} and body: {body}")

    async def get_sent_messages(self, branch_id: str) -> list[EmailCompose]:
        """
            get all Sent Messages for a specific Branch
        :param branch_id:
        :return:
        """
        with self.get_session() as session:
            email_messages_orm = session.query(EmailComposeORM).filter_by(to_branch=branch_id).all()
            return [EmailCompose(**email.to_dict()) for email in email_messages_orm
                    if isinstance(email, EmailComposeORM)]

    async def get_sent_email(self, message_id: str) -> EmailCompose | None:
        """
            Get a Specific Sent Email from the database
        :param message_id:
        :return:
        """
        with self.get_session() as session:
            email_message_orm = session.query(EmailComposeORM).filter_by(message_id=message_id).first()
            if isinstance(email_message_orm, EmailComposeORM):
                return EmailCompose(**email_message_orm.to_dict())
            return None


class SMSService(Controllers):
    def __init__(self):
        super().__init__()
        self.sms_service_api = None
        self.twilio_number = None
        # Inbox Messages
        self.inbox_queue: dict[str: list[SMSInbox]] = {}
        # Sent Messages
        self.sent_messages_queue: dict[str: list[SMSCompose]] = {}
        # a dict of reference or message_id from the api provider matched with the branch_id in the application
        self.sent_references: dict[str: list[str]] = {}

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, settings: Settings):

        super().init_app(app=app)
        self.sms_service_api = Client(settings.TWILIO.TWILIO_SID, settings.TWILIO.TWILIO_TOKEN)
        self.twilio_number = settings.TWILIO.TWILIO_NUMBER

    async def check_incoming_sms_api(self) -> list[SMSInbox]:
        """
            for whichever SMS API i am using map the message to SMS Inbox and return
        :return:
        """
        # TODO Complete the API Implementation to fetch incoming SMS Messages Here
        if self.sms_service_api:
            # Use the References to match incoming messages to previously sent messages in order to identify responses
            for branch_id, references in self.sent_references:
                for message_sent_reference in references:
                    # save each reference used when constructing the inboxMessage
                    pass

        return []

    async def send_sms(self, composed_sms: SMSCompose):
        """
            Sending the SMS Messages to the Outside World this will feed the Sent Box
        :param composed_sms:
        :return:
        """
        # Code to send SMS via SMS service API
        self.logger.info(f"Sending SMS to {composed_sms.to_cell} with message: {composed_sms.message}")

        if self.sms_service_api:
            # API is initialized do send message
            # Sending SMS with Twilio
            sent_reference = self.sms_service_api.messages.create(
                to=composed_sms.to_cell,
                from_=self.twilio_number,
                body=composed_sms.message
            )
            self.logger.info(f"SID : {sent_reference}")
            composed_sms.reference = sent_reference
            sent_references = self.sent_references.get(composed_sms.to_branch, [])
            sent_references.append(sent_reference)
            self.sent_references[composed_sms.to_branch] = sent_references

        composed_sms.date_time_sent = date_time()

        # Sent Messages will read from this Queue
        composed_messages: list[SMSCompose] = self.sent_messages_queue.get(composed_sms.to_branch, [])
        composed_messages.append(composed_sms)

        self.sent_messages_queue[composed_sms.to_branch] = composed_messages

        # Saving Sent Messages to the Database
        with self.get_session() as session:
            session.add(SMSComposeORM(**composed_sms.dict()))
            session.commit()

        # Simulate sending SMS asynchronously
        # await asyncio.sleep(1)
        self.logger.info("SMS sent successfully")

    async def retrieve_sms_responses_service(self):
        """
            Fetching the SMS Messages which are sent to this company or as responses
            this will feed the inbox
        :return:
        """
        # Code to receive SMS from SMS service API
        if self.sms_service_api:

            # Message Retrieved from API
            incoming__messages: list[SMSInbox] = await self.check_incoming_sms_api()

            for message in incoming__messages:
                inbox_messages: list[SMSInbox] = self.inbox_queue.get(message.to_branch, [])

                sent_references: list[str] = self.sent_references[message.to_branch]
                sent_references.remove(message.parent_reference)
                self.sent_references[message.to_branch] = sent_references
                original_message = await self.mark_message_as_responded(reference=message.parent_reference)
                message.previous_history += f"""
                -------------------------------------------------------------------------------------------------------
                date_response : {date_time()}
                
                original_message:

                {original_message.message}
                """

                inbox_messages.append(message)
                self.inbox_queue[message.to_branch] = inbox_messages

                # Storing the Message to Database
                await self.store_sms_to_database_inbox(sms_message=message)

    async def store_sms_to_database_inbox(self, sms_message: SMSInbox) -> SMSInbox:
        with self.get_session() as session:
            session.add(SMSInboxORM(**sms_message.dict()))
            session.commit()
            return sms_message

    async def get_inbox_messages_from_database(self, branch_id: str) -> list[SMSInbox]:
        with self.get_session() as session:
            inbox_list = session.query(SMSInboxORM).filter_by(to_branch=branch_id).all()
            return [SMSInbox(**inbox.to_dict()) for inbox in inbox_list if isinstance(inbox, SMSInboxORM)]

    async def get_sent_box_messages_from_database(self, branch_id: str) -> list[SMSCompose]:
        with self.get_session() as session:
            compose_orm_list = session.query(SMSComposeORM).filter_by(to_branch=branch_id).all()
            return [SMSCompose(**sms.to_dict()) for sms in compose_orm_list if isinstance(sms, SMSComposeORM)]

    async def mark_message_as_responded(self, reference: str) -> SMSCompose | None:
        with self.get_session() as session:
            message_orm = session.query(SMSComposeORM).filter_by(reference=reference).first()
            if isinstance(message_orm, SMSComposeORM):
                sms_compose = SMSCompose(**message_orm.to_dict())
                message_orm.client_responded = True
                message_orm.is_delivered = True

                sms_compose.is_delivered = True
                sms_compose.client_responded = True
                session.commit()

                return sms_compose
            return None

    async def add_sms_settings(self, settings: SMSSettings) -> SMSSettings:
        """

        :param settings:
        :return:
        """
        with self.get_session() as session:
            sms_settings_orm = session.query(SMSSettingsORM).filter_by(company_id=settings.company_id).first()
            if isinstance(sms_settings_orm, SMSSettingsORM):
                # Update the existing record
                sms_settings_orm.enable_sms_notifications = settings.enable_sms_notifications
                sms_settings_orm.enable_sms_campaigns = settings.enable_sms_campaigns
                sms_settings_orm.sms_signature = settings.sms_signature
                sms_settings_orm.policy_lapsed_notifications = settings.policy_lapsed_notifications
                sms_settings_orm.upcoming_payments_notifications = settings.upcoming_payments_notifications
                sms_settings_orm.policy_paid_notifications = settings.policy_paid_notifications
                sms_settings_orm.claims_notifications = settings.claims_notifications
            else:
                # Create a new record
                new_sms_settings = SMSSettingsORM(**settings.dict())
                session.add(new_sms_settings)

            session.commit()

            return settings

    async def get_sms_settings(self, company_id: str) -> SMSSettings | None:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            sms_settings_orm = session.query(SMSSettingsORM).filter_by(company_id=company_id).first()
            if isinstance(sms_settings_orm, SMSSettingsORM):
                return SMSSettings(**sms_settings_orm.to_dict())
            return None


class WhatsAppService(Controllers):
    def __init__(self):
        super().__init__()
        self.whatsapp_api = None
        self.twilio_number = None

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, settings: Settings):
        super().init_app(app=app)
        self.whatsapp_api = Client(settings.TWILIO.TWILIO_SID, settings.TWILIO.TWILIO_TOKEN)
        self.twilio_number = settings.TWILIO.TWILIO_NUMBER

    async def send_whatsapp_message(self, recipient: str, message: str):
        # Code to send WhatsApp message via WhatsApp service API
        self.logger.info(f"Sending WhatsApp message to {recipient} with message: {message}")
        # Simulate sending WhatsApp message asynchronously
        # await asyncio.sleep(3)
        self.logger.info("WhatsApp message sent successfully")

    async def receive_whatsapp_message(self, sender: str, message: str):
        # Code to receive WhatsApp message from WhatsApp service API
        self.logger.info(f"Received WhatsApp message from {sender} with message: {message}")


class MessagingController(Controllers):
    def __init__(self, ):

        super().__init__()
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.whatsapp_service = WhatsAppService()

        self.email_queue = asyncio.Queue()
        self.sms_queue = asyncio.Queue()
        self.whatsapp_queue = asyncio.Queue()

        self.loop = asyncio.get_event_loop()
        self.burst_delay = 2
        self.timer_multiplier = 60
        self.timer_limit = 60
        self.event_triggered_time = 0
        self.stop_event = asyncio.Event()

    # ------------------------------------------------------------------------------------------------------------------

    async def get_sms_inbox(self, branch_id: str) -> list[SMSInbox]:

        return self.sms_service.inbox_queue.get(branch_id, [])

    # noinspection PyMethodOverriding
    def init_app(self, app: Flask, settings: Settings, emailer: SendMail):
        """
        :param app:
        :param settings:
        :param emailer:
        :return:
        """
        super().init_app(app=app)
        # Initializing communication Services
        self.email_service.init_app(app=app, settings=settings, emailer=emailer)
        self.sms_service.init_app(app=app, settings=settings)
        self.whatsapp_service.init_app(app=app, settings=settings)

        self.loop.create_task(self.messaging_daemon())
        self.logger.info("Loop Initialized")

    async def send_email(self, email: EmailCompose):
        """
            This only adds the outgoing email to the Queue
        :param email:
        :return:
        """
        # Convert Compose Email to Email Sending Model
        # email_model = EmailModel(to_=email.to_email, subject_=email.subject, html_=email.message)
        await self.email_queue.put(email)
        await self.cancel_sleep()

    async def send_sms(self, composed_sms: SMSCompose):
        await self.sms_queue.put(composed_sms)
        self.logger.info(f"SMS in Queue : {composed_sms}")
        await self.cancel_sleep()

        return True

    async def send_whatsapp_message(self, recipient: str, message: str):
        await self.whatsapp_queue.put((recipient, message))
        await self.cancel_sleep()
        return True

    async def process_email_queue(self):
        # self.logger.info("Processing Email")
        if self.email_queue.empty():
            # self.logger.info("No Email Messages")
            return
        self.logger.info("Started Processing Email Queue")
        total_emails_sent = 0
        while not self.email_queue.empty():
            email: EmailCompose = await self.email_queue.get()
            await self.email_service.send_email(email=email)
            await asyncio.sleep(delay=self.burst_delay)
            self.email_queue.task_done()
            total_emails_sent += 1
        self.logger.info(f"Sent {str(total_emails_sent)} Email Messages")

    async def process_sms_queue(self):

        # self.logger.info("processing sms outgoing message queues")
        if self.sms_queue.empty():
            # self.logger.info("no sms messages to send")
            return
        self.logger.info("started processing SMS Queue")
        while not self.sms_queue.empty():
            composed_sms: SMSCompose = await self.sms_queue.get()
            response = await self.sms_service.send_sms(composed_sms=composed_sms)
            await asyncio.sleep(delay=self.burst_delay)  # sleep for
            # response will carry a response message from the api provider at this point
            # TO
            self.sms_queue.task_done()
        self.logger.info("Processing SMS Queue: Completed")

    async def process_whatsapp_queue(self):

        # self.logger.info("processing whatsapp out going message queues")
        if self.whatsapp_queue.empty():
            # self.logger.info("No WhatsAPP Messages")
            return

        while not self.whatsapp_queue.empty():
            recipient, message = await self.whatsapp_queue.get()

            await self.whatsapp_service.send_whatsapp_message(recipient, message)
            await asyncio.sleep(delay=self.burst_delay)

            self.whatsapp_queue.task_done()

    async def cancel_sleep(self):
        """External method to cancel the sleep."""
        time_now = time.time_ns()
        self.timer_multiplier = 1
        # Calculate the elapsed time since the last event trigger
        elapsed_time = (time_now - self.event_triggered_time) / 1e9  # Convert nanoseconds to seconds

        if elapsed_time >= 300:  # 300 seconds is 5 minutes
            self.event_triggered_time = time_now
            self.stop_event.set()
            self.logger.info('triggered cancel sleep event')
        else:
            pass
            # self.logger.info('cancel sleep event not triggered: too soon')

    async def messaging_daemon(self):
        self.logger.info("Thread Started-------------------------------------------------")
        i = 0
        time_started = time.time()

        async def standard_time(start_time) -> str:
            time_elapsed = time.time() - start_time
            hours = int(time_elapsed // 3600)
            minutes = int((time_elapsed % 3600) // 60)
            seconds = int(time_elapsed % 60)
            return f"{hours} hours, {minutes} minutes, {seconds} seconds"

        while True:
            # Out Going Message Queues
            self.logger.info("Loop restarted................................")
            i += 1
            await self.process_email_queue()
            await self.process_sms_queue()
            await self.process_whatsapp_queue()

            # Incoming Message Queues
            self.logger.info("Started Processing Incoming Messages")
            await self.sms_service.retrieve_sms_responses_service()

            # This Means the loop will run every 5 minutes
            display_time = await standard_time(time_started)
            self.logger.info(f"Counter {str(i)}--------------------------- Time Elapsed : {display_time}")
            # await asyncio.sleep(60 * timer_multiplier)

            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=60 * self.timer_multiplier)

                if self.stop_event.is_set():
                    self.logger.info("continue with execution as stop event is triggered")

                    self.stop_event.clear()  # Reset the event

                # This Ensures that the timer will keep increasing until its one hour long
                if self.timer_multiplier < self.timer_limit:
                    self.timer_multiplier += 2

            except asyncio.TimeoutError:
                # If the timeout happens without the event being set, we just continue
                pass
