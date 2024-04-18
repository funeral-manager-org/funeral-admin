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
    branch_uid: str
    company_uid: str

    policy_number: str = Field(default_factory=create_policy_number)
    plan_number: str
    policy_type: list[ClaimType]

    total_family_members: int
    total_premiums: int
    payment_code_reference: str
    date_activated: str
    first_premium_date: str
    payment_day: int
    client_signature: str
    employee_signature: str

    payment_method: str
    relation_to_policy_holder: RelationshipToPolicyHolder
    policy_active: bool = Field(default=False)
    is_policy_holder: bool = Field(default=False)


class ClientPersonalInformation(BaseModel):
    uid: str = Field(default_factory=create_id)
    branch_uid: str
    company_uid: str

    title: str
    full_names: str
    surname: str
    id_number: str
    date_of_birth: str
    nationality: str

    address_id: str
    contact_id: str
    postal_id: str

    bank_account_id: str


class ClaimStatus(Enum):
    REJECTED = "Rejected"
    APPROVED = "Approved"
    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"


class Claims(BaseModel):
    uid: str
    employee_id: str | None
    branch_uid: str
    company_uid: str
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
