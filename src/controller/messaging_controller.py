import asyncio
from src.controller import error_handler, Controllers
from flask import Flask


class EmailService:

    def __init__(self):
        pass

    async def send_email(self, recipient: str, subject: str, body: str):
        # Code to send email via email service API
        print(f"Sending email to {recipient} with subject: {subject} and body: {body}")
        # Simulate sending email asynchronously
        await asyncio.sleep(2)
        print("Email sent successfully")

    async def receive_email(self, sender: str, subject: str, body: str):
        # Code to receive email from email service API
        print(f"Received email from {sender} with subject: {subject} and body: {body}")


class SMSService:
    def __init__(self):
        pass
    async def send_sms(self, recipient: str, message: str):
        # Code to send SMS via SMS service API
        print(f"Sending SMS to {recipient} with message: {message}")
        # Simulate sending SMS asynchronously
        await asyncio.sleep(1)
        print("SMS sent successfully")

    async def receive_sms(self, sender: str, message: str):
        # Code to receive SMS from SMS service API
        print(f"Received SMS from {sender} with message: {message}")


class WhatsAppService:
    def __init__(self):
        pass
    async def send_whatsapp_message(self, recipient: str, message: str):
        # Code to send WhatsApp message via WhatsApp service API
        print(f"Sending WhatsApp message to {recipient} with message: {message}")
        # Simulate sending WhatsApp message asynchronously
        await asyncio.sleep(3)
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
        print(f"putting message to Queue : {message}")
        await self.sms_queue.put((recipient, message))

    async def send_whatsapp_message(self, recipient: str, message: str):
        await self.whatsapp_queue.put((recipient, message))

    async def process_email_queue(self):
        while True:
            print("is is processing email")
            recipient, subject, body = await self.email_queue.get()
            await self.email_service.send_email(recipient, subject, body)
            self.email_queue.task_done()

    async def process_sms_queue(self):
        while True:
            print("is is processing SMS")
            recipient, message = await self.sms_queue.get()
            await self.sms_service.send_sms(recipient, message)
            self.sms_queue.task_done()

    async def process_whatsapp_queue(self):
        while True:
            print("is is processing Whastapp")
            recipient, message = await self.whatsapp_queue.get()
            await self.whatsapp_service.send_whatsapp_message(recipient, message)
            self.whatsapp_queue.task_done()

    async def start_processing(self):
        await asyncio.gather(
            self.process_email_queue(),
            self.process_sms_queue(),
            self.process_whatsapp_queue()
        )

    async def start_app(self):
        await self.start_processing()

