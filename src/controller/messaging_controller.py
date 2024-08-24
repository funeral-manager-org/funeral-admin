
import asyncio
import time
from datetime import datetime

import requests
from flask import Flask
from twilio.rest import Client
import vonage
from src.config import Settings
from src.controller import Controllers, error_handler
from src.database.models.messaging import SMSInbox, EmailCompose, SMSCompose, SMSSettings
from src.database.sql.messaging import SMSInboxORM, SMSComposeORM, EmailComposeORM, SMSSettingsORM
from src.emailer import EmailModel, SendMail
from src.main import system_cache
from src.utils import create_id

cached_ttl = system_cache.cached_ttl


def date_time() -> str:
    """"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def standard_time(start_time: float) -> str:
    """
    Calculate and return the elapsed time since the given start time in hours, minutes, and seconds.

    :param start_time: The start time in seconds since the epoch (e.g., as returned by `time.time()`).
    :return: A string representing the elapsed time in the format "X hours, Y minutes, Z seconds".
    """
    # Calculate the total elapsed time in seconds
    elapsed_seconds = time.time() - start_time

    # Calculate hours, minutes, and seconds
    hours = elapsed_seconds // 3600  # Number of complete hours
    minutes = (elapsed_seconds % 3600) // 60  # Number of complete minutes remaining
    seconds = elapsed_seconds % 60  # Number of remaining seconds

    # Return the formatted time as a string
    return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"


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
            if response:
                self.logger.info(f"Sent Email Response : {response}")
                self.sent_email_queue[response.get('id', create_id())] = email_
                # Saving Sent Message to the Database
                await self.store_sent_email_to_database(email_)
            else:
                self.logger.error(f"Email not sent : {str(email)}")

            await system_cache.clear_mem_cache()
        except requests.exceptions.ConnectTimeout:
            self.logger.error("Resend Connection TimeOut")
            await asyncio.sleep(delay=self.cool_down_on_error)
            await self.send_email(email=email)

    @error_handler
    async def store_sent_email_to_database(self, email_: EmailCompose):
        await system_cache.clear_mem_cache()
        with self.get_session() as session:
            sent_email_orm = EmailComposeORM(**email_.dict(exclude={'html_template'}))
            session.add(sent_email_orm)

    async def receive_email(self, sender: str, subject: str, body: str):
        # Code to receive email from email service API
        self.logger.info(f"Received email from {sender} with subject: {subject} and body: {body}")

    @cached_ttl()
    @error_handler
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

    @cached_ttl(ttl=360)
    @error_handler
    async def get_sent_email_paged(self, branch_id: str, page: int, count: int) -> list[EmailCompose]:
        """
        Get paged Sent Messages for a specific Branch
        :param branch_id: Branch ID to filter messages
        :param page: Page number to retrieve
        :param count: Number of messages per page
        :return: List of paged EmailCompose instances
        """
        with self.get_session() as session:
            email_messages_orm = (
                session.query(EmailComposeORM)
                .filter_by(to_branch=branch_id)
                .offset(page * count)
                .limit(count)
                .all()
            )
            return [EmailCompose(**email.to_dict()) for email in email_messages_orm
                    if isinstance(email, EmailComposeORM)]

    @cached_ttl()
    @error_handler
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
        self.can_use_vonage = True
        self.can_use_twilio = False
        self.vonage_api = None
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
        self.vonage_api: vonage.Client = vonage.Client(key=settings.VONAGE.API_KEY, secret=settings.VONAGE.SECRET)

    async def get_vonage_balance(self) -> int:
        """
            **get_vonage_balance**
        :return:
        """
        return self.vonage_api.account.get_balance()

    async def check_incoming_sms_api(self) -> list[SMSInbox]:
        """
            for whichever SMS API i am using map the message to SMS Inbox and return
        :return:
        """
        # TODO Complete the API Implementation to fetch incoming SMS Messages Here
        if self.sms_service_api or self.vonage_api:
            # Use the References to match incoming messages to previously sent messages in order to identify responses
            for branch_id in self.sent_references.keys():
                for message_reference in self.sent_references[branch_id]:
                    # save each reference used when constructing the inboxMessage
                    # https://funeral-manager.org/api/v1/vonage/sms-status
                    # TODO-  should check vonage of twilio if a message was delivered
                    self.logger.info(f"Sent Message ID : {message_reference}")
                    if self.can_use_vonage:
                        pass

        return []

    async def send_with_vonage(self, composed_sms: SMSCompose) -> str:

        response = self.vonage_api.messages.send_message({
            'channel': 'sms',
            'message_type': 'text',
            'to': composed_sms.to_cell_vonage_za,
            'from': 'vonage',
            'text': composed_sms.message
        })

        self.logger.info(f"VONAGE RESPONSE : {response}")
        return response.get('message_uuid')

    async def send_with_twilio(self, composed_sms: SMSCompose) -> str:
        """
            **send_with_twilio**
            will use twilio APi to send messages to end users
        :param composed_sms:
        :return:
        """
        return self.sms_service_api.messages.create(
            to=composed_sms.to_cell,
            from_=self.twilio_number,
            body=composed_sms.message
        )

    async def send_sms(self, composed_sms: SMSCompose):
        """
            Sending the SMS Messages to the Outside World this will feed the Sent Box
        :param composed_sms:
        :return:
        """
        # Code to send SMS via SMS service API
        self.logger.info(f"Sending SMS to {composed_sms.to_cell} with message: {composed_sms.message}")

        if self.vonage_api and self.can_use_vonage:
            sent_reference = await self.send_with_vonage(composed_sms=composed_sms)
            if composed_sms.to_branch not in self.sent_references:
                self.sent_references[composed_sms.to_branch] = []
            self.sent_references[composed_sms.to_branch].append(sent_reference)
            self.logger.info(f"Sent References Initial Structure : {self.sent_references}")

        elif self.sms_service_api and self.can_use_twilio:
            sent_reference = await self.send_with_twilio(composed_sms=composed_sms)
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
        self.logger.info("SMS sent successfully")

    async def retrieve_sms_responses_service(self):
        """
            Fetching the SMS Messages which are sent to this company or as responses
            this will feed the inbox
        :return:
        """
        # Code to receive SMS from SMS service API
        if self.sms_service_api or self.vonage_api:
            # Message Retrieved from API
            incoming__messages: list[SMSInbox] = await self.check_incoming_sms_api()
            for message in incoming__messages:
                inbox_messages: list[SMSInbox] = self.inbox_queue.get(message.to_branch, [])

                sent_references: list[str] = self.sent_references[message.to_branch]
                sent_references.remove(message.parent_reference)
                self.sent_references[message.to_branch] = sent_references
                original_message = await self.mark_message_as_responded(reference=message.parent_reference)
                message.previous_history += f"""
                ---------------------------------------------------------------------------------------------
                    date_response : {date_time()}            
                    original_message:
                    {original_message.message}
                """
                inbox_messages.append(message)
                self.inbox_queue[message.to_branch] = inbox_messages

                # Storing the Message to Database
                await self.store_sms_to_database_inbox(sms_message=message)

    @error_handler
    async def store_sms_to_database_inbox(self, sms_message: SMSInbox) -> SMSInbox:
        with self.get_session() as session:
            session.add(SMSInboxORM(**sms_message.dict()))
            await system_cache.clear_mem_cache()
            return sms_message

    @cached_ttl()
    @error_handler
    async def get_inbox_messages_from_database(self, branch_id: str) -> list[SMSInbox]:
        with self.get_session() as session:
            inbox_list = session.query(SMSInboxORM).filter_by(to_branch=branch_id).all()
            return [SMSInbox(**inbox.to_dict()) for inbox in inbox_list if isinstance(inbox, SMSInboxORM)]

    @cached_ttl()
    @error_handler
    async def get_sent_box_messages_from_database(self, branch_id: str) -> list[SMSCompose]:
        with self.get_session() as session:
            compose_orm_list = session.query(SMSComposeORM).filter_by(to_branch=branch_id).all()
            return [SMSCompose(**sms.to_dict()) for sms in compose_orm_list if isinstance(sms, SMSComposeORM)]

    @cached_ttl()
    @error_handler
    async def get_sent_box_messages_paged(self, branch_id: str, page: int, count: int) -> list[SMSCompose]:
        with self.get_session() as session:
            offset = page * count
            compose_orm_list = (session.query(SMSComposeORM)
                                .filter_by(to_branch=branch_id)
                                .offset(offset)
                                .limit(count)
                                .all())
            return [SMSCompose(**sms.to_dict()) for sms in compose_orm_list if isinstance(sms, SMSComposeORM)]

    @error_handler
    async def mark_message_as_responded(self, reference: str) -> SMSCompose | None:
        with self.get_session() as session:
            message_orm = session.query(SMSComposeORM).filter_by(reference=reference).first()
            await system_cache.clear_mem_cache()

            if isinstance(message_orm, SMSComposeORM):
                sms_compose = SMSCompose(**message_orm.to_dict())
                message_orm.client_responded = True
                message_orm.is_delivered = True

                sms_compose.is_delivered = True
                sms_compose.client_responded = True

                return sms_compose
            return None

    @error_handler
    async def add_sms_settings(self, settings: SMSSettings) -> SMSSettings:
        """
            **add_sms_settings*8
        :param settings:
        :return:
        """
        with self.get_session() as session:
            sms_settings_orm = session.query(SMSSettingsORM).filter_by(company_id=settings.company_id).first()
            await system_cache.clear_mem_cache()
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

            return settings

    @cached_ttl()
    @error_handler
    async def get_sms_settings(self, company_id: str) -> SMSSettings | None:
        """
            **get_sms_settings**
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
        self.whatsapp_api = vonage.Client(key=settings.VONAGE.API_KEY, secret=settings.VONAGE.SECRET)
        self.twilio_number = settings.TWILIO.TWILIO_NUMBER

    async def send_whatsapp_message(self, from_number: str, recipient: str, message: str) -> str:
        # Code to send WhatsApp message via WhatsApp service API
        self.logger.info(f"Sending WhatsApp message to {recipient} with message: {message}")
        # Simulate sending WhatsApp message asynchronously
        # await asyncio.sleep(3)
        response = self.whatsapp_api.messages.send_message({
            "channel": "whatsapp",
            "message_type": "text",
            "to": recipient,
            "from": from_number,
            "text": message

        })
        self.logger.info("WhatsApp message sent successfully")
        return response.get('message_uuid')

    async def receive_whatsapp_message(self, sender: str, message: str):
        # Code to receive WhatsApp message from WhatsApp service API
        self.logger.info(f"Received WhatsApp message from {sender} with message: {message}")


class MessagingController(Controllers):
    def __init__(self):

        super().__init__()
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.whatsapp_service = WhatsAppService()

        self.email_queue = asyncio.Queue()
        self.sms_queue = asyncio.Queue()
        self.whatsapp_queue = asyncio.Queue()

        self.loop = asyncio.get_event_loop()
        self.burst_delay = 2
        self.timer_multiplier = 1
        self.timer_limit = 60 * 60 * 1
        self.event_triggered_time = 0
        self.cancel_await_event = asyncio.Event()

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

    async def send_whatsapp_message(self, from_number: str, recipient: str, message: str):
        await self.whatsapp_queue.put((from_number, recipient, message))
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
            if email:
                await self.email_service.send_email(email=email)
            await asyncio.sleep(delay=self.burst_delay)
            self.email_queue.task_done()
            total_emails_sent += 1
        self.logger.info(f"Sent {str(total_emails_sent)} Email Messages")

    async def process_sms_queue(self):
        # self.logger.info("processing sms outgoing message queues")
        while not self.sms_queue.empty():
            try:
                composed_sms: SMSCompose = await self.sms_queue.get()
                if composed_sms:
                    _ = await self.sms_service.send_sms(composed_sms=composed_sms)
                    await asyncio.sleep(delay=self.burst_delay)  # sleep for response
                    self.sms_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing SMS queue: {e}")
        self.logger.info("Processing SMS Queue: Completed")

    async def process_whatsapp_queue(self):
        # self.logger.info("processing whatsapp out going message queues")
        if self.whatsapp_queue.empty():
            # self.logger.info("No WhatsAPP Messages")
            return

        while not self.whatsapp_queue.empty():
            from_number, recipient, message = await self.whatsapp_queue.get()
            await self.whatsapp_service.send_whatsapp_message(from_number, recipient, message)
            await asyncio.sleep(delay=self.burst_delay)
            self.whatsapp_queue.task_done()

    async def cancel_sleep(self):
        """External method to cancel the sleep."""
        time_now = time.time_ns()
        self.timer_multiplier = 1
        # Calculate the elapsed time since the last event trigger
        elapsed_time = (time_now - self.event_triggered_time) / 1e9  # Convert nanoseconds to seconds

        if elapsed_time >= 30:  # 60 seconds is 1 minutes
            self.event_triggered_time = time_now
            self.cancel_await_event.set()
            self.logger.info('Triggered cancel sleep event')
        else:
            pass
            # self.logger.info('cancel sleep event not triggered: too soon')

    import asyncio

    async def messaging_daemon(self):
        self.logger.info("Thread Started-------------------------------------------------")
        wait_time = 60 * 1  # 10 minutes
        while True:
            if self.cancel_await_event.is_set():
                self.logger.info("Cancel event triggered, processing immediately")
                self.cancel_await_event.clear()  # Reset the event for next use

            # Check for cancel event immediately
            await self.run_events()
            try:
                await asyncio.wait_for(self.cancel_await_event.wait(), timeout=wait_time)
            except asyncio.TimeoutError:
                pass

    async def run_events(self):
        # Outgoing Message Queues
        self.logger.info("started running tasks")
        # Create a list of tasks for outgoing message queues
        tasks = [self.process_email_queue(),self.process_sms_queue(),self.process_whatsapp_queue()]
        # Run the tasks concurrently
        await asyncio.gather(*tasks)
        await self.sms_service.retrieve_sms_responses_service() # Removed the commented-out await asyncio.sleep line
        self.logger.info("completed this round")
        # Handle incoming SMS responses
