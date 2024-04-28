from datetime import date
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
