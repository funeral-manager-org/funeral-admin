from enum import Enum

from pydantic import BaseModel, Field

from utils import create_id, create_policy_number, create_claim_number


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
    GROCERIES = "GROCERIES"
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

class ClientResidentialAddresses(BaseModel):
    uid: str
    branch_uid: str
    company_uid: str

    address_line_1: str
    address_line_2: str
    country: str
    town_city: str
    province: str
    postal_code: str


class ClientPostalAddresses(BaseModel):
    uid: str
    branch_uid: str
    company_uid: str

    address_line_1: str
    town_city: str
    province: str
    country: str
    postal_code: str


class ClientContactDetails(BaseModel):
    uid: str
    branch_uid: str
    company_uid: str

    cell: str
    tel: str
    email: str
    facebook: str
    twitter: str
    whatsapp: str


class ClientBankDetails(BaseModel):
    uid: str
    branch_uid: str
    company_uid: str

    bank_name: str
    account_holder: str
    account_number: str
    account_type: str
    branch_code: str


class ClaimStatus(Enum):
    REJECTED = "Rejected"
    APPROVED = "Approved"
    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"


class Claims(BaseModel):
    uid: str
    branch_uid: str
    company_uid: str
    claim_number: str = Field(default_factory=create_claim_number)
    plan_number: str
    policy_number: str

    claim_amount: int
    claim_total_paid: int
    claimed_for_uid: str
    date_paid: str
    claim_status: ClaimStatus

    funeral_company: str
    claim_type: ClaimType  # Add a field for the claim type
