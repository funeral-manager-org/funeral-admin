import asyncio
import time
import timeit

from flask import Flask

from src.controller import Controllers
from src.database.models.messaging import SMSInbox
from src.database.sql.messaging import SMSInboxORM


class EmailService:

    def __init__(self):
        pass

    async def send_email(self, recipient: str, subject: str, body: str):
        # Code to send email via email service API
        print(f"Sending email to {recipient} with subject: {subject} and body: {body}")
        # Simulate sending email asynchronously
        # await asyncio.sleep(2)
        print("Email sent successfully")

    async def receive_email(self, sender: str, subject: str, body: str):
        # Code to receive email from email service API
        print(f"Received email from {sender} with subject: {subject} and body: {body}")


class SMSService(Controllers):
    def __init__(self):
        super().__init__()
        self.sms_service_api = None
        self.inbox_queue = asyncio.Queue()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def check_incoming_sms_api(self) -> SMSInbox:
        """
            for whichever SMS API i am using map the message to SMS Inbox and return
        :return:
        """
        pass

    async def send_sms(self, recipient: str, message: str):
        # Code to send SMS via SMS service API
        print(f"Sending SMS to {recipient} with message: {message}")
        # Simulate sending SMS asynchronously
        # await asyncio.sleep(1)
        print("SMS sent successfully")

    async def retrieve_sms_service(self):
        # Code to receive SMS from SMS service API
        if self.sms_service_api:
            # Message Retrieved from API
            message: SMSInbox = await self.check_incoming_sms_api()

            # Putting the Message to the inbox Queue
            await self.inbox_queue.put(message)
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
            return [SMSInbox(**inbox.to_dict()) for inbox in inbox_list]


class WhatsAppService:
    def __init__(self):
        pass

    async def send_whatsapp_message(self, recipient: str, message: str):
        # Code to send WhatsApp message via WhatsApp service API
        print(f"Sending WhatsApp message to {recipient} with message: {message}")
        # Simulate sending WhatsApp message asynchronously
        # await asyncio.sleep(3)
        print("WhatsApp message sent successfully")

    async def receive_whatsapp_message(self, sender: str, message: str):
        # Code to receive WhatsApp message from WhatsApp service API
        print(f"Received WhatsApp message from {sender} with message: {message}")


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

    def init_app(self, app: Flask):
        super().init_app(app=app)
        self.loop.create_task(self.start_app())
        print("Loop Initialized")

    async def send_email(self, recipient: str, subject: str, body: str):
        await self.email_queue.put((recipient, subject, body))

    async def send_sms(self, recipient: str, message: str):
        print(f"Putting Message to Queue : {message}")
        await self.sms_queue.put((recipient, message))
        # print(await self.sms_queue.get())
        return True

    async def send_whatsapp_message(self, recipient: str, message: str):
        await self.whatsapp_queue.put((recipient, message))
        return True

    async def process_email_queue(self):
        print("Processing Email")
        if self.email_queue.empty():
            print("No Email Messages")
            return

        recipient, subject, body = await self.email_queue.get()
        await self.email_service.send_email(recipient, subject, body)
        self.email_queue.task_done()

    async def process_sms_queue(self):

        print("processing sms outgoing message queues")
        if self.sms_queue.empty():
            print("No SMS Messages")
            return
        recipient, message = await self.sms_queue.get()

        await self.sms_service.send_sms(recipient, message)
        self.sms_queue.task_done()

    async def process_whatsapp_queue(self):

        print("processing whatsapp out going message queues")
        if self.whatsapp_queue.empty():
            print("No WhatsAPP Messages")
            return

        recipient, message = await self.whatsapp_queue.get()
        await self.whatsapp_service.send_whatsapp_message(recipient, message)
        self.whatsapp_queue.task_done()

    async def start_app(self):
        print("Thread Started-------------------------------------------------")
        i = 0
        time_started = time.time()

        async def standard_time(time_elapsed: float) -> str:
            hours = int(time_elapsed // 3600)
            minutes = int((time_elapsed % 3600) // 60)
            seconds = int(time_elapsed % 60)
            return f"{hours} hours, {minutes} minutes, {seconds}"

        while True:
            # Out Going Message Queues
            i += 1
            await self.process_email_queue(),
            await self.process_sms_queue(),
            await self.process_whatsapp_queue()

            # Incoming Message Queues
            await self.sms_service.retrieve_sms_service()

            # This Means the loop will run every 5 minutes
            await asyncio.sleep(60*5)

            time_elapsed = time.time() - time_started
            display_time = await standard_time(time_elapsed=time_elapsed)
            print(f"Counter {str(i)}--------------------------- Time Elapsed : {display_time}")
