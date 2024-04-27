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
    company_id: str | None

    plan_number: str = Field(default_factory=create_plan_number)
    plan_name: str
    plan_type: str

    benefits: str
    coverage_amount: int
    premium_costs: int
    additional_details: str
    terms_and_conditions: str
    inclusions: str
    exclusions: str
    contact_information: str


###########################################################################################
##### EMPLOYEE ROLES
###########################################################################################

class EmployeeRoles:
    ADMIN = 'Administrator'
    DIRECTOR = 'Funeral Director'
    RECEPTIONIST = 'Receptionist'
    ACCOUNTANT = 'Accountant'
    MORTICIAN = 'Mortician'
    SUPPORT_STAFF = 'Support Staff'
    SERVICE_MANAGER = 'Service Manager'  # New role for managing extra services
    @classmethod
    def get_all_roles(cls):
        return [value for name, value in vars(cls).items() if not name.startswith('__') and isinstance(value, str)]


class EmployeePermissions:
    # Existing permissions
    VIEW_CLIENT_INFO = 'View/Edit Client Information'
    SCHEDULE_APPOINTMENTS = 'Schedule Appointments'
    CREATE_INVOICES = 'Create/Manage Invoices'
    MANAGE_INVENTORY = 'Manage Inventory'
    VIEW_FINANCIAL_REPORTS = 'View Financial Reports'
    ACCESS_EMPLOYEE_RECORDS = 'Access Employee Records'
    GENERATE_REPORTS = 'Generate Reports'
    ADMIN_TASKS = 'Perform System Administration Tasks'

    # New permissions for extra services
    MANAGE_EXTRA_SERVICES = 'Manage Extra Services'
    VIEW_SERVICE_COVERS = 'View Service Covers'


class Employee:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.permissions = set()

    def add_permission(self, permission):
        self.permissions.add(permission)

    def has_permission(self, permission):
        return permission in self.permissions


# Define employee roles
employee_roles = {
    EmployeeRoles.ADMIN: [EmployeePermissions.VIEW_CLIENT_INFO, EmployeePermissions.SCHEDULE_APPOINTMENTS,
                          EmployeePermissions.CREATE_INVOICES, EmployeePermissions.MANAGE_INVENTORY,
                          EmployeePermissions.VIEW_FINANCIAL_REPORTS, EmployeePermissions.ACCESS_EMPLOYEE_RECORDS,
                          EmployeePermissions.GENERATE_REPORTS, EmployeePermissions.ADMIN_TASKS],

    EmployeeRoles.DIRECTOR: [EmployeePermissions.VIEW_CLIENT_INFO, EmployeePermissions.SCHEDULE_APPOINTMENTS,
                             EmployeePermissions.CREATE_INVOICES, EmployeePermissions.MANAGE_INVENTORY,
                             EmployeePermissions.ACCESS_EMPLOYEE_RECORDS],

    EmployeeRoles.RECEPTIONIST: [EmployeePermissions.VIEW_CLIENT_INFO, EmployeePermissions.SCHEDULE_APPOINTMENTS],

    EmployeeRoles.ACCOUNTANT: [EmployeePermissions.CREATE_INVOICES, EmployeePermissions.VIEW_FINANCIAL_REPORTS],

    EmployeeRoles.MORTICIAN: [EmployeePermissions.VIEW_CLIENT_INFO, EmployeePermissions.MANAGE_INVENTORY],

    EmployeeRoles.SUPPORT_STAFF: [EmployeePermissions.VIEW_CLIENT_INFO],

    EmployeeRoles.SERVICE_MANAGER: [EmployeePermissions.MANAGE_EXTRA_SERVICES, EmployeePermissions.VIEW_SERVICE_COVERS]
}


class EmployeeDetails(BaseModel):
    """
    Represents details about an employee.

    Attributes:
        employee_id (str): The ID of the employee.
        company_id (str): The ID of the company to which the employee belongs.
        branch_id (str): The ID of the branch to which the employee is assigned.
        full_names (str): The first name and middle name of the employee.
        last_name (str): The last name or surname of the employee.
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
    company_id: str | None
    branch_id: str | None

    full_names: str
    last_name: str
    id_number: str
    role: str
    email: str
    contact_number: str
    position: str
    role: str
    date_of_birth: str
    date_joined: str = Field(default_factory=string_today)
    salary: int
    is_active: bool = True

    address_id: str | None
    contact_id: str | None
    postal_id: str | None
    bank_account_id: str | None

