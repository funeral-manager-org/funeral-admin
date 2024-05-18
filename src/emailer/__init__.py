from flask import Flask
from datetime import datetime
from pydantic import BaseModel
import resend

from src.database.models.messaging import EmailCompose
from src.config import config_instance

settings = config_instance().EMAIL_SETTINGS

def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class EmailModel(BaseModel):
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

    def init_app(self, app: Flask):
        pass

    async def send_mail_resend(self, email: EmailCompose | EmailModel) -> tuple[dict[str, str], EmailCompose]:
        if isinstance(email, EmailCompose):
            params = {'from': self.from_ or email.from_email, 'to': email.to_email, 'subject': email.subject,
                      'html': email.message}

            email.from_email = self.from_
            email.date_time_sent = date_time()
            email.is_sent = True
        else:
            params = {'from': self.from_, 'to': email.to_, 'subject':email.subject_, 'html': email.html_}
        print(f"Params : {params}")

        response: dict[str, str] = self._resend.Emails.send(params=params)

        return response, email
