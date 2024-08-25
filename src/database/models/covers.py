import math
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from enum import Enum
from pydantic import BaseModel, Field
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


class InsuredParty(Enum):
    POLICY_HOLDER = "Policy Holder"
    BENEFICIARY = "Beneficiary"
    DEPENDENT = "DEPENDENT"

    @classmethod
    def get_client_types(cls) -> list[str]:
        return [method.value for method in cls]


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

    insured_party: str | None = Field(default=None)
    relation_to_policy_holder: str | None = Field(default=None)
    plan_number: str | None = Field(default=None)
    policy_number: str | None = Field(default=None)

    address_id: str | None = Field(default=None)
    contact_id: str | None = Field(default=None)
    postal_id: str | None = Field(default=None)

    bank_account_id: str | None = Field(default=None)

    @property
    def client_display_name(self):
        return f"{self.full_names} {self.surname}"

    @property
    def is_policy_holder(self):
        return self.insured_party == InsuredParty.POLICY_HOLDER.value


class ClaimStatus(Enum):
    REJECTED = "Rejected"
    APPROVED = "Approved"
    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"

# 8101245336238 , J0AYTC03Y
class BeginClaim(BaseModel):
    policy_number: str = Field(min_length=9, max_length=9)
    id_number: str = Field(min_length=13, max_length=13)


class Claims(BaseModel):
    claim_number: str = Field(default_factory=create_claim_number)
    uid: str
    employee_id: str | None
    branch_id: str
    company_id: str
    plan_number: str
    policy_number: str

    claim_amount: int
    claim_total_paid: int
    claimed_for_uid: str | None = Field(default=None)
    date_paid: str
    claim_status: ClaimStatus

    funeral_company: str
    claim_type: ClaimType  # Add a field for the claim type
    notes: str | None


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
    today = datetime.now().date().replace(day=1)
    return today + relativedelta(months=1)


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

    premium_id: str = Field(default_factory=create_id)
    policy_number: str
    scheduled_payment_date: date = Field(default_factory=lambda: datetime.now().date())

    payment_amount: int = Field(default=0)
    amount_paid: int = Field(default=0)
    date_paid: date = Field(default_factory=lambda: datetime.now().date())

    payment_method: str = Field(default=PaymentMethods.intermediary.value)
    payment_status: str = Field(default=PaymentStatus.DUE.value)
    next_payment_amount: int = Field(default=0)
    next_payment_date: date = Field(default_factory=next_due_date)
    payment_frequency: str = Field(default=PaymentFrequency.MONTHLY.value)

    def __bool__(self) -> bool:
        return bool(self.premium_id)

    def update_payment_status(self):
        if (self.balance_due < 1) or self.is_paid:
            self.payment_status = PaymentStatus.PAID.value
        elif self.balance_due > 0 and self.is_payment_overdue:
            self.payment_status = PaymentStatus.OVERDUE.value
        else:
            self.payment_status = PaymentStatus.DUE.value
        print(f"Updated payment Status : {self.payment_status}")

    @property
    def is_payment_overdue(self) -> bool:
        return not self.is_paid and datetime.now().date() > (
                self.scheduled_payment_date + relativedelta(days=self.late_payment_threshold_days))

    @property
    def checked_payment_status(self) -> str:
        self.update_payment_status()
        return self.payment_status

    @property
    def is_paid(self) -> bool:
        return self.amount_paid >= self.total_due > 0

    @property
    def late_payment_days(self) -> int:
        return max((self.date_paid - self.scheduled_payment_date).days, 0)

    @property
    def late_payment_charges(self) -> int:
        if self.late_payment_days >= self.late_payment_threshold_days:
            charged_per_threshold = int(self.payment_amount * (self.percent_charged / 100))
            max_charges = int(charged_per_threshold * 4)
            return min((self.late_payment_days // self.late_payment_threshold_days) * charged_per_threshold,
                       max_charges)
        return 0

    @property
    def total_due(self) -> int:
        return self.payment_amount + self.late_payment_charges

    @property
    def balance_due(self) -> int:
        return self.total_due - self.amount_paid


class PremiumReceipt(BaseModel):
    receipt_number: str = Field(default_factory=create_id)
    premium_id: str

    datetime_paid: datetime = Field(default_factory=datetime.now)
    paid_amount: int = Field(default=0)
    policy_number: str
    sms_notification_sent: bool = Field(default=False)
    email_notification_sent: bool = Field(default=False)
    whatsapp_notification_sent: bool = Field(default=False)
    premium: Premiums | None = Field(default=None)

    @classmethod
    def from_premium(cls, premium: Premiums) -> 'PremiumReceipt':
        return cls(
            premium_id=premium.premium_id,
            paid_amount=premium.amount_paid,
            policy_number=premium.policy_number
        )


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
    date_activated: str | None = Field(default=None)
    first_premium_date: str | None = Field(default=None)
    payment_day: int | None = Field(default=None)
    client_signature: str | None = Field(default=None)
    employee_signature: str | None = Field(default=None)

    payment_method: str | None = Field(default=None)
    policy_active: bool = Field(default=False)
    premiums: list[Premiums] = Field(default=[])

    @property
    def sorted_premiums(self) -> list[Premiums]:
        """returns premiums sorted in ascending order by premium date"""
        return sorted(self.premiums, key=lambda _premium: _premium.scheduled_payment_date)

    @property
    def total_balance_due(self) -> int:
        """The total amount of money owed to the funeral company"""
        today = datetime.today().date()
        return sum((premium.balance_due for premium in self.premiums
                    if ((premium.scheduled_payment_date <= today) and (not premium.is_paid))))

    @property
    def out_standing(self) -> bool:
        this_month_premium = self.get_this_month_premium()
        if not this_month_premium:
            return True
        this_month_premium.update_payment_status()
        # outstanding because the latest premium is overdue
        if this_month_premium.payment_status == PaymentStatus.OVERDUE.value:
            return True

        # check if any other premium was not paid before
        return self.total_balance_due > self.total_premiums

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
        if today is within seven days of reminders being tried then send the reminders
        :return: True if notification can be sent, otherwise False.
        """
        if self.payment_day is None:
            return False

        # Calculate the difference in days
        day_difference = (self.payment_day - this_day()) % 31

        # Check if the difference is within the 5 to 7-day window
        return 5 <= day_difference <= 7

    def next_payment_date(self) -> date | None:
        """
        Determine the next payment date.
        """
        if self.premiums:
            today = datetime.now().date()
            next_payment_date = max(premium.next_payment_date for premium in self.sorted_premiums)

            if today <= next_payment_date:
                return next_payment_date

        today: date = datetime.now().date()
        if self.payment_day is not None:
            current_month_due_date: date = today.replace(day=self.payment_day)

            if today.day <= self.payment_day:
                # Payment Day has not yet passed and Premium not paid
                return current_month_due_date
            else:
                # returns next month due date
                return current_month_due_date + relativedelta(months=1)
        return None  # Default to None if no payment_day is specified

    def get_this_month_premium(self) -> Premiums | None:
        """will return premium model for this month"""
        if not self.premiums:
            return None
        for premium in self.sorted_premiums:
            if premium.scheduled_payment_date.month == datetime.now().month:
                return premium
        return None

    @staticmethod
    def report_month_in_words() -> str:
        months_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'}
        return months_names[datetime.now().month]

    def get_previous_month_premium(self) -> Premiums | None:
        """will return previous month premium if exist"""
        if not self.premiums:
            return None
        last_month_date: date = datetime.now().date() - relativedelta(months=1)
        for premium in self.sorted_premiums:
            if premium.scheduled_payment_date.month == last_month_date.month:
                return premium
        return None

    def get_first_unpaid(self) -> Premiums | None:
        """will return the first premium which is not paid"""
        if not self.premiums:
            return None
        # Find the first unpaid premium
        for premium in self.sorted_premiums:
            if not premium.is_paid:
                return premium
        return None  # Return None if all premiums are paid

    def next_payment_amount(self) -> int | None:
        """
            will return the premium for next month if available
        :return:
        """
        if not self.premiums:
            return None
        next_month_date: date = datetime.now().date() + relativedelta(months=1)
        for premium in self.sorted_premiums:
            if premium.scheduled_payment_date.month == next_month_date.month:
                return premium.payment_amount
        return None

    def next_month_premium(self) -> Premiums | None:
        """returns next months Premium"""
        if not self.premiums:
            return None
        next_month_date: date = datetime.now().date() + relativedelta(months=1)
        for premium in self.sorted_premiums:
            if premium.scheduled_payment_date.month == next_month_date.month:
                return premium
        return None
