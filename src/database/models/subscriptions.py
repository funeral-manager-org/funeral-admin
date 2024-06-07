from enum import Enum

from pydantic import BaseModel, Field
from datetime import datetime

from src.database.models.payments import Payment
from src.utils import create_id


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PlanNames(Enum):
    FREE = "FREE"
    BUSINESS = "BUSINESS"
    PREMIUM = "PREMIUM"

    @classmethod
    def plan_names(cls):
        return [cls.FREE.value, cls.BUSINESS.value, cls.PREMIUM.value]


class SubscriptionDetails(BaseModel):
    plan_name: str = ""
    total_sms: int = Field(default=20)
    total_emails: int = Field(default=50)
    total_clients: int = Field(default=250)
    subscription_amount: int = Field(default=0)
    subscription_period: int = Field(default=1)
    additional_clients: int = Field(default=0)

    def create_plan(self, plan_name: str):
        self.plan_name = plan_name
        if plan_name == PlanNames.FREE.value:
            self.total_sms = 20
            self.total_emails = 50
            self.total_clients = 250
            self.subscription_amount = 0
            self.subscription_period = 1
            self.additional_clients = 10
        elif plan_name == PlanNames.BUSINESS.value:
            self.total_sms = 500
            self.total_emails = 500
            self.total_clients = 500
            self.subscription_amount = 1500
            self.subscription_period = 1
            self.additional_clients = 10
        elif plan_name == PlanNames.PREMIUM.value:
            self.total_sms = 2000
            self.total_emails = 1000
            self.total_clients = 1000
            self.subscription_amount = 3000
            self.subscription_period = 1
            self.additional_clients = 5
        else:
            self.total_sms = 20
            self.total_emails = 50
            self.total_clients = 250
            self.subscription_amount = 0
            self.subscription_period = 1
            self.additional_clients = 10

        return self


class Subscriptions(BaseModel):
    company_id: str
    subscription_id: str = Field(default_factory=create_id)
    plan_name: str
    total_sms: int
    total_emails: int
    total_clients: int
    date_subscribed: str = Field(default_factory=date_time)
    subscription_amount: int
    subscription_period: int
    payments: list[Payment] = []

    @property
    def subscribed_date(self):
        try:
            if self.date_subscribed:
                return datetime.strptime(self.date_subscribed, '%Y-%m-%d')
            else:
                self.date_subscribed = date_time()
                return datetime.strptime(self.date_subscribed, '%Y-%m-%d')
        except ValueError:
            # Handle error, possibly log it and return None or a default datetime
            return None

    @property
    def is_paid_for_current_month(self) -> bool:
        """Checks if the subscription has been paid for the current month"""
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year

        for payment in self.payments:
            payment_date = payment.date_paid
            if payment.is_successful and payment_date.month == current_month and payment_date.year == current_year:
                return True

        return False

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
        """Will return True if subscription is expired"""
        date_bought_dt = datetime.fromisoformat(self.date_subscribed)
        current_date = datetime.now()
        months_diff = (current_date.year - date_bought_dt.year) * 12 + current_date.month - date_bought_dt.month

        return months_diff > self.subscription_period

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
