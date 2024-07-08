import math
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from ulid import ULID

from enum import Enum
from pydantic import BaseModel, Field, validator
from src.utils import create_id, create_policy_number, create_claim_number


def create_ulid() -> str:
    """
    Generate a ULID (Universally Unique Lexicographically Sortable Identifier).
    """
    return str(ULID.from_datetime(datetime.now()))


class PaymentMethods(Enum):
    direct_deposit = "Direct Deposit"
    payroll = "Payroll"
    debit_order = "Debit Order"
    persal_deduction = "Persal Deduction"
    intermediary = "Intermediary"
    declaration = "Declaration"

    @classmethod
    def get_payment_methods(cls):
        return [method.value for method in cls]


class RelationshipToPolicyHolder(Enum):
    SELF = "Self"
    SPOUSE = "Spouse"
    CHILD = "Child"
    PARENT = "Parent"
    GRANDPARENT = "Grandparent"
    SIBLING = "Sibling"
    OTHER_RELATIVE = "Other Relative"
    FRIEND = "Friend"
    BUSINESS_PARTNER = "Business Partner"
    OTHER = "Other"


class ClaimType(Enum):
    MONEY = "Money"
    SERVICES = "Services"
    GROCERIES = "Groceries"
    BOTH = "Both"


class InsuredParty(Enum):
    POLICY_HOLDER = "Policy Holder"
    BENEFICIARY = "Beneficiary"
    DEPENDENT = "DEPENDENT"


class ClientPersonalInformation(BaseModel):
    uid: str = Field(default_factory=create_id)
    branch_id: str
    company_id: str

    title: str
    full_names: str
    surname: str

    id_number: str
    date_of_birth: str
    nationality: str

    insured_party: str | None
    relation_to_policy_holder: str | None
    plan_number: str | None
    policy_number: str | None

    address_id: str | None
    contact_id: str | None
    postal_id: str | None

    bank_account_id: str | None


class ClaimStatus(Enum):
    REJECTED = "Rejected"
    APPROVED = "Approved"
    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"


class Claims(BaseModel):
    uid: str
    employee_id: str | None
    branch_id: str
    company_id: str
    claim_number: str = Field(default_factory=create_claim_number)
    plan_number: str
    policy_number: str

    claim_amount: int
    claim_total_paid: int
    claimed_for_uid: str | None
    date_paid: str
    claim_status: ClaimStatus

    funeral_company: str
    claim_type: ClaimType  # Add a field for the claim type


def this_year() -> int:
    """Return the current year."""
    return datetime.now().year


def this_month() -> int:
    """Return the current month."""
    return datetime.now().month


def this_day() -> int:
    """Return the current day of the month."""
    return datetime.now().day


def next_due_date(days_offset: int = 30) -> date:
    """Return the next due date, defaulting to 30 days from today."""
    return datetime.now().date() + timedelta(days=days_offset)


class PaymentStatus(str, Enum):
    PAID = "Paid"
    DUE = "Due"
    OVERDUE = "Overdue"


class PaymentFrequency(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"


class Premiums(BaseModel):
    late_payment_threshold_days: int = Field(default=10)
    percent_charged: int = Field(default=5)

    premium_id: str = Field(default_factory=create_ulid)
    policy_number: str
    scheduled_payment_date: date = Field(default_factory=datetime.now().date)

    payment_amount: int = Field(default=0)
    amount_paid: int = Field(default=0)
    date_paid: date = Field(default_factory=datetime.now().date)

    payment_method: str = Field(default=PaymentMethods.intermediary.value)
    payment_status: str = Field(default=PaymentStatus.DUE.value)
    next_payment_amount: int = Field(default=0)
    next_payment_date: date = Field(default_factory=next_due_date)
    payment_frequency: str = Field(default=PaymentFrequency.MONTHLY.value)

    @property
    def is_paid(self) -> bool:
        return int(self.amount_paid) >= int(self.payment_amount) > 0

    @property
    def late_payment_days(self) -> int:
        """
        Calculate the number of late payment days.
        """
        if self.date_paid > self.scheduled_payment_date:
            return (self.date_paid - self.scheduled_payment_date).days
        return 0

    @property
    def late_payment_charges(self) -> int:
        """
        Calculate the late payment charges based on the number of late days.
        """

        if self.late_payment_days >= self.late_payment_threshold_days:
            charged_per_threshold = self.payment_amount * (self.percent_charged / 100)
            max_charges = int(charged_per_threshold * 4)
            return min(int((self.late_payment_days // self.late_payment_threshold_days) * charged_per_threshold),
                       max_charges)
        return 0

    @property
    def total_due(self) -> int:
        return self.payment_amount + self.late_payment_charges

    @property
    def balance_due(self) -> int:
        return self.total_due - self.amount_paid


class PremiumInvoice(BaseModel):
    invoice_number: str = Field(default_factory=create_ulid)
    premium_id: str

    datetime_paid: datetime = Field(default_factory=datetime.now())
    paid_amount: int = Field(default=0)
    policy_number: str
    secondary_cell: str
    payment_notification_sent: bool = Field(default=False)


class PolicyRegistrationData(BaseModel):
    uid: str
    branch_id: str
    company_id: str

    policy_number: str = Field(default_factory=create_policy_number)
    plan_number: str
    policy_type: str

    total_family_members: int = Field(default=0)
    total_premiums: int
    payment_code_reference: str = Field(default_factory=create_policy_number)
    date_activated: str | None
    first_premium_date: str | None
    payment_day: int | None
    client_signature: str | None
    employee_signature: str | None

    payment_method: str | None
    policy_active: bool = Field(default=False)
    premiums: list[Premiums] | None

    @property
    def total_balance_due(self) -> int:
        """
        The total amount of money owed to the funeral company
        """
        today = datetime.today().date()

        return sum((premium.balance_due for premium in self.premiums
                    if ((premium.scheduled_payment_date <= today) and (not premium.is_paid))))

    def total_future_payments(self, include_previous: bool = False, total_months: int = 3) -> int:
        """
            # this method is assuming that Premiums Records are already present for the future months
            forecasted payments for three monhts in default
            if include previous is True the total will include total balance due
        :param include_previous:
        :param total_months:
        :return:
        """
        today = datetime.today().date()
        end_date = today + relativedelta(months=total_months)
        future_payments = sum(premium.balance_due for premium in self.premiums or []
                              if ((premium.scheduled_payment_date <= end_date) and not premium.is_paid))
        if include_previous:
            future_payments += self.total_balance_due
        return future_payments

    def can_send_payment_reminder(self) -> bool:
        """
        Check if the payment notification can be sent.
        Notification can be sent if the current date is within 7 days before the payment_day.

        :return: True if notification can be sent, otherwise False.
        """
        if self.payment_day is None:
            return False

        # Get the current day of the month
        today = datetime.today().day

        # Calculate the difference in days
        day_difference = (self.payment_day - today) % 31

        # Check if the difference is within the 5 to 7-day window
        return 5 <= day_difference <= 7

    def next_payment_date(self) -> date:
        """
        Determine the next payment date.
        """
        if self.premiums:
            today = datetime.today().date()
            next_payment_date = max(premium.next_payment_date for premium in self.premiums)

            if today <= next_payment_date:
                return next_payment_date

        today = datetime.today().date()
        if self.payment_day is not None:
            current_month_due_date = today.replace(day=self.payment_day)
            if today.day <= self.payment_day:
                return current_month_due_date
            else:
                next_month_due_date = current_month_due_date + relativedelta(months=1)
                return next_month_due_date
        return today  # Default to today if no payment_day is specified

    def get_this_month_premium(self):
        if not self.premiums:
            return None
        for premium in self.premiums:
            if premium.scheduled_payment_date.month == datetime.now().month:
                return premium
        return None

    def get_first_unpaid(self):
        if not self.premiums:
            return None
        # Sort premiums by scheduled_payment_date
        self.premiums = sorted(self.premiums, key=lambda premium: premium.scheduled_payment_date)
        # Find the first unpaid premium
        for premium in self.premiums:
            if not premium.is_paid:
                return premium
        return None  # Return None if all premiums are paid

    def next_payment_amount(self):
        if self.premiums:
            pass
