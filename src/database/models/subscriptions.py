from enum import Enum

from pydantic import BaseModel, Field, PositiveInt
from datetime import datetime, date, timedelta

from src.database.models.payments import Payment
from src.utils import create_id, create_reference


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PlanNames(Enum):
    BASIC = "BASIC"
    BUSINESS = "BUSINESS"
    PREMIUM = "PREMIUM"
    ULTIMATE = "ULTIMATE"

    @classmethod
    def plan_names(cls):
        return [cls.BASIC.value, cls.BUSINESS.value, cls.PREMIUM.value,cls.ULTIMATE.value]


class SubscriptionDetails(BaseModel):
    """
        Currency Amounts are in South African Rands
    """
    plan_name: str = ""
    total_sms: int = Field(default=20)
    total_emails: int = Field(default=50)
    total_clients: int = Field(default=250)
    subscription_amount: int = Field(default=0)
    subscription_period: int = Field(default=1)
    additional_clients: int = Field(default=0)

    def create_plan(self, plan_name: str):
        self.plan_name = plan_name.upper()
        if plan_name == PlanNames.BASIC.value:
            self.total_sms = 200
            self.total_emails = 500
            self.total_clients = 250
            self.subscription_amount = 500
            self.subscription_period = 1
            self.additional_clients = 10
        elif plan_name == PlanNames.BUSINESS.value:
            self.total_sms = 500
            self.total_emails = 500
            self.total_clients = 1000
            self.subscription_amount = 1500
            self.subscription_period = 1
            self.additional_clients = 10
        elif plan_name == PlanNames.PREMIUM.value:
            self.total_sms = 2000
            self.total_emails = 1000
            self.total_clients = 3000
            self.subscription_amount = 3000
            self.subscription_period = 1
            self.additional_clients = 5
        elif plan_name == PlanNames.ULTIMATE.value:
            self.total_sms = 5000
            self.total_emails = 10000
            self.total_clients = 100000
            self.subscription_amount = 9000
            self.subscription_period = 1
            self.additional_clients = 5
        else:
            self.total_sms = 20
            self.total_emails = 50
            self.total_clients = 250
            self.subscription_amount = 50
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
    reference: str| None = Field(default_factory=create_reference)

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
    def subscribed_datetime(self):
        return self.date_subscribed
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


class Package(BaseModel):
    package_id: str = Field(default_factory=create_id)
    company_id: str
    package_name: str
    total_sms: int = Field(default=0)
    total_email: int = Field(default=0)
    is_paid: bool = Field(default=False)
    is_added: bool = Field(default=False)
    total_amount: PositiveInt = Field(default=0)
    date_bought: str = Field(default_factory=date_time)
    payments: list[Payment]| None = Field(default=[])

    def use_package(self) -> int:
        if self.is_paid and not self.is_added:
            remaining = self.total_sms
            self.total_sms = 0
            return remaining
        return 0


def this_day() -> datetime:
    """
    :return:
    """
    return datetime.today()


class SubscriptionStatus(BaseModel):
    id: str = Field(default_factory=create_id)
    last_checked: date = Field(default_factory=this_day)

    def subscription_checked_recently(self) -> bool:
        """Check if the subscription has been checked for the current week."""
        if not self.last_checked:
            return False

        now = datetime.now().date()
        three_days_ago = date.today() - timedelta(days=3)
        return self.last_checked >= three_days_ago


class PaymentNoticeInterval(BaseModel):
    """
        this keeps track of payment notices sent for each company and when they where sent
    """
    company_id: str
    last_payment_notice_sent_date: date | None = Field(default=None)
    last_expired_notice_sent_date: date | None = Field(default=None)

    def payment_notice_sent_within_three_days(self) -> bool:
        """Check if a payment notice was sent within the last three days."""
        if not self.last_payment_notice_sent_date:
            return False

        three_days_ago = date.today() - timedelta(days=3)
        return self.last_payment_notice_sent_date >= three_days_ago

    def payment_expired_notice_sent_within_three_days(self) -> bool:
        """

        :return:
        """
        if not self.last_expired_notice_sent_date:
            return False
        three_days_ago = date.today() - timedelta(days=3)
        return self.last_expired_notice_sent_date >= three_days_ago


class TopUpNames(Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


class TopUpTypes(Enum):
    SMS = "sms"
    EMAIL = "email"


class TopUpPacks(BaseModel):
    package_id: str = Field(default_factory=create_id)
    company_id: str
    top_up_type: str
    top_up_name: str

    @property
    def plan_name(self):
        return f"{self.top_up_type}_{self.top_up_name}"

    @property
    def total_sms(self):
        sms_limits = {
            TopUpNames.BASIC.value: 1500,
            TopUpNames.PROFESSIONAL.value: 4000,
            TopUpNames.PREMIUM.value: 8000
        }
        return sms_limits.get(self.top_up_name, 0) if self.top_up_type == TopUpTypes.SMS.value else 0

    @property
    def total_emails(self):
        email_limits = {
            TopUpNames.BASIC.value: 1500,
            TopUpNames.PROFESSIONAL.value: 4000,
            TopUpNames.PREMIUM.value: 8000

        }
        return email_limits.get(self.top_up_name, 0) if self.top_up_type == TopUpTypes.EMAIL.value else 0

    @property
    def payment_amount(self):
        sms_payment_amounts = {
            TopUpNames.BASIC.value: 540,
            TopUpNames.PROFESSIONAL.value: 900,
            TopUpNames.PREMIUM.value: 1400
        }
        email_payment_amounts = {
            TopUpNames.BASIC.value: 540,
            TopUpNames.PROFESSIONAL.value: 900,
            TopUpNames.PREMIUM.value: 1400
        }
        if self.top_up_type == TopUpTypes.SMS.value:
            return sms_payment_amounts.get(self.top_up_name, 0)
        if self.top_up_type == TopUpTypes.EMAIL.value:
            return email_payment_amounts.get(self.top_up_name, 0)
        return 0
