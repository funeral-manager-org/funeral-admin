from enum import Enum

from pydantic import BaseModel, Field
from datetime import datetime

from src.utils import create_id


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Subscriptions(BaseModel):
    company_id: str
    plan_name: str
    total_sms: int
    total_emails: int
    total_clients: int
    date_subscribed: str
    subscription_amount: int
    subscription_period: int

    def take_sms_credit(self):
        if self.total_sms:
            self.total_sms -= 1
        return self.total_sms

    def take_email_credit(self):
        if self.total_emails:
            self.total_emails -= 1
        return self.total_emails

    def take_client_credit(self):
        if self.total_clients:
            self.total_clients -= 1
        return self.total_clients

    def is_expired(self) -> bool:
        date_bought_dt = datetime.fromisoformat(self.date_subscribed)
        current_date = datetime.now()
        months_diff = (current_date.year - date_bought_dt.year) * 12 + current_date.month - date_bought_dt.month

        return months_diff >= self.subscription_period


class SMSPackage(BaseModel):
    package_id: str = Field(default_factory=create_id)
    company_id: str
    package_name: str
    total_sms: int
    is_paid: bool = Field(default=False)
    is_added: bool = Field(default=False)
    date_bought: str = Field(default_factory=date_time)

    def use_package(self) -> int:
        if self.is_paid and not self.is_added:
            remaining = self.total_sms
            self.total_sms = 0
            return remaining
        return 0
