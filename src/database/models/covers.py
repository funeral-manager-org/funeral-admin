from datetime import date, datetime, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
from src.utils import create_id, create_policy_number, create_claim_number


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

    def return_next_payment_date(self):
        """
        Return the next payment date as a tuple containing the day name and date.

        :return: (day_name, date_str) where day_name is the name of the day and date_str is the date in YYYY-MM-DD format.
        """
        if self.payment_day is None:
            return None

        today = datetime.today()
        current_month_days = (today.replace(day=28) + timedelta(days=4)).day

        # Calculate the next payment date
        if today.day <= self.payment_day:
            next_payment_date = today.replace(day=self.payment_day)
        else:
            # Handle month wrap-around
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year if today.month < 12 else today.year + 1
            if self.payment_day > current_month_days:
                self.payment_day = current_month_days
            next_payment_date = datetime(next_year, next_month, self.payment_day)

        # Get the day name and formatted date string
        day_name = next_payment_date.strftime('%A')
        date_str = next_payment_date.strftime('%Y-%m-%d')

        return day_name, date_str


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
    # Historical data fields
    premium_id: str = Field(default_factory=create_id)
    policy_number: str

    amount_paid: int = Field(default=0)
    late_payment_charges: int = Field(default=0)
    payment_method: str = Field(default="Unknown")

    payment_date: date = Field(default_factory=datetime.now().date)
    payment_status: str = Field(default=PaymentStatus.DUE.value)

    year_paid: int = Field(default_factory=this_year)
    month_paid: int = Field(default_factory=this_month)
    day_paid: int = Field(default_factory=this_day)

    next_payment_amount: int = Field(default=0)
    next_payment_date: date = Field(default_factory=next_due_date)

    payment_frequency: str = Field(default=PaymentFrequency.MONTHLY.value)

    @validator('next_payment_date', pre=True, always=True)
    def calculate_next_payment_date(cls, v, values):
        """Calculate the next payment date based on last payment date and frequency."""
        if 'payment_date' in values and values['payment_date']:
            frequency = values.get('payment_frequency', PaymentFrequency.MONTHLY.value)
            if frequency == PaymentFrequency.MONTHLY.value:
                return values['payment_date'] + relativedelta(months=1)
            elif frequency == PaymentFrequency.QUARTERLY.value:
                return values['payment_date'] + relativedelta(months=3)
            elif frequency == PaymentFrequency.ANNUALLY.value:
                return values['payment_date'] + relativedelta(years=1)
        return v

    # def calculate_late_payment_charges(self) -> int:
    #     """Calculate the late payment charges based on overdue period."""
    #     if self.payment_status == PaymentStatus.OVERDUE:
    #         days_overdue = (datetime.now().date() - self.next_payment_date).days
    #         if days_overdue > 0:
    #             periods = days_overdue // 10
    #             return int(self.next_payment_amount * 0.05 * periods)
    #     return 0
    #
    # @validator('late_payment_charges', always=True)
    # def update_late_payment_charges(cls, v, values):
    #     """Update the late payment charges based on the current date."""
    #     premium_instance = Premiums(**values)
    #     return premium_instance.calculate_late_payment_charges()
