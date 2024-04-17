from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from utils import create_id, string_today, create_plan_number


class Company(BaseModel):
    company_id: str = Field(default_factory=create_id)
    admin_uid: str
    company_name: str
    company_description: str
    company_slogan: str
    date_registered: str = Field(default_factory=string_today)
    total_users: int = Field(default=1)
    total_clients: int = Field(default=0)


class CompanyBranches(BaseModel):
    branch_id: str = Field(default_factory=create_id)
    company_id: str
    branch_name: str
    branch_description: str
    date_registered: str = Field(default_factory=string_today)
    total_users: int = Field(default=1)
    total_clients: int = Field(default=0)

class PlanTypes(BaseModel):
    """
        User defined model to allow managers to create their own plan types
    """
    branch_id: str
    company_id: str

    plan_number: str
    plan_type: str

class CoverPlanDetails(BaseModel):
    """
    Represents details about a funeral cover plan.

    Attributes:
        branch_id (str): The ID of the branch associated with the plan.
        company_id (str): The ID of the company offering the plan.
        plan_name (str): The name of the funeral cover plan.
        plan_type (str): The type of funeral cover plan (e.g., "Individual", "Family", "Group").
        benefits (List[str]): List of benefits provided by the plan.
        coverage_amount (int): Amount covered by the plan.
        premium_costs (int): Cost of premiums for the plan.
        additional_details (str): Additional details about the plan.
        terms_and_conditions (str): Terms and conditions associated with the plan.
        inclusions (List[str]): List of inclusions provided by the plan.
        exclusions (List[str]): List of exclusions from the plan.
        contact_information (str): Contact information for inquiries about the plan.
        policy_registration_data (PolicyRegistrationData): Policy registration data associated with the plan.
    """
    branch_id: str
    company_id: str

    plan_number: str = Field(default_factory=create_plan_number)
    plan_name: str
    plan_type: str

    benefits: list[str]
    coverage_amount: int
    premium_costs: int
    additional_details: str
    terms_and_conditions: str
    inclusions: list[str]
    exclusions: list[str]
    contact_information: str
