
from pydantic import BaseModel, Field
from src.utils import create_id, string_today, create_plan_number, create_employee_id


class Company(BaseModel):
    company_id: str = Field(default_factory=create_id)
    admin_uid: str
    reg_ck: str
    vat_number: str | None
    company_name: str
    company_description: str
    company_slogan: str
    date_registered: str = Field(default_factory=string_today)
    total_users: int = Field(default=1)
    total_clients: int = Field(default=0)


class CompanyBranches(BaseModel):
    """

    """
    branch_id: str = Field(default_factory=create_id)
    company_id: str
    branch_name: str
    branch_description: str
    date_registered: str = Field(default_factory=string_today)
    total_clients: int = Field(default=0)
    total_employees: int = Field(default=1)

    address_id: str | None
    contact_id: str | None
    postal_id: str | None
    bank_account_id: str | None




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


class EmployeeDetails(BaseModel):
    """
    Represents details about an employee.

    Attributes:
        employee_id (str): The ID of the employee.
        company_id (str): The ID of the company to which the employee belongs.
        branch_id (str): The ID of the branch to which the employee is assigned.
        first_name (str): The first name of the employee.
        last_name (str): The last name of the employee.
        email (str): The email address of the employee.
        contact_number (str): The contact number of the employee.
        position (str): The position or role of the employee.
        date_of_birth (str): The date of birth of the employee.
        date_joined (str): The date when the employee joined the company.
        salary (float): The salary of the employee.
        is_active (bool): Indicates whether the employee is currently active or not.
    """
    employee_id: str = Field(default_factory=create_employee_id)

    uid: str | None
    company_id: str
    branch_id: str

    first_name: str
    last_name: str
    email: str
    contact_number: str
    position: str
    date_of_birth: str
    date_joined: str = Field(default_factory=string_today)
    salary: float
    is_active: bool = True
