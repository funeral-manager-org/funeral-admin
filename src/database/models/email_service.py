import uuid
from datetime import date

from pydantic import BaseModel, Field, Extra


def create_id():
    return str(uuid.uuid4())


class EmailService(BaseModel):
    subscription_id: str = Field(default_factory=create_id)
    uid: str
    email: str
    email_stub: str
    subscription_term: int
    total_emails: int
    subscription_active: bool = Field(default=False)
    subscription_running: bool = Field(default=False)

    @property
    def total_amount(self) -> int:
        prices = {
            3: {10: 15, 25: 30, 50: 45, 100: 60},
            6: {10: 25, 25: 40, 50: 55, 100: 70},
            12: {10: 35, 25: 50, 50: 65, 100: 80}
        }

        return prices.get(self.subscription_term, {}).get(self.total_emails, 0)

    class Config:
        extra = Extra.ignore


class EmailSubscriptions(BaseModel):
    subscription_id: str = Field(default_factory=create_id)
    email_address: str
    map_to: str
    is_used: bool = Field(default=False)
    date_used: date| None
