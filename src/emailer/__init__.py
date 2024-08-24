from flask import Flask
from datetime import datetime
from pydantic import BaseModel
import resend

from src.logger import init_logger
from src.database.models.messaging import EmailCompose
from src.config import config_instance
from src.utils import create_id,camel_to_snake

settings = config_instance().EMAIL_SETTINGS


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class EmailModel(BaseModel):
    reference: str | None
    from_: str | None
    to_: str | None
    subject_: str
    html_: str


class SendMail:
    """
        Make this more formal
    """

    def __init__(self):
        self._resend = resend
        self._resend.api_key = settings.RESEND.API_KEY
        self.from_: str | None = settings.RESEND.from_
        self.logger = init_logger(camel_to_snake(self.__class__.__name__))

    def init_app(self, app: Flask):
        pass

    async def send_mail_resend(self, email: EmailCompose | EmailModel) -> tuple[dict[str, str], EmailCompose]:
        if isinstance(email, EmailCompose):
            params = {'from': self.from_ or email.from_email, 'to': email.to_email, 'subject': email.subject,
                      'html': email.html_template or email.message}

            email.from_email = self.from_
            email.date_time_sent = date_time()
            email.is_sent = True
        else:
            params = {'from': self.from_, 'to': email.to_, 'subject': email.subject_, 'html': email.html_}
        # print(f"Params : {params}")
        try:
            response: dict[str, str] = self._resend.Emails.send(params=params)
            email.reference = response.get('id', create_id())
            return response, email
        except Exception as e:
            self.logger.error(f"Error Resend API Not Working : Sending Email : {str(e)}")
        return None, None