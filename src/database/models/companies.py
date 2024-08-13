import calendar
from datetime import datetime, date, timedelta
from typing import Optional, Union, TypeVar

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, EmailStr
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


class TimeRecord(BaseModel):
    time_id: str = Field(default_factory=create_id)
    attendance_id: str
    normal_minutes_per_session: int = Field(default=8 * 60)
    clock_in: datetime
    clock_out: datetime | None

    @property
    def normal_minutes_worked(self) -> int:
        """
        Calculates the total minutes worked based on clock_in and clock_out times.
        Handles cases where clock_out falls on the next day.

        Returns:
            int: Total minutes worked.
        """
        if not self.clock_in or not self.clock_out:
            return 0  # Handle missing clock in/out times
        # Calculate the difference in time
        delta: timedelta = self.clock_out - self.clock_in
        return min(int(delta.total_seconds() // 60), self.normal_minutes_per_session)

    @property
    def overtime_worked(self) -> int:
        """
        if normal_minutes worked is less than normal minutes per work session
        then overtime is zero - else overtime is the difference
            :return:
        """
        return max(self.normal_minutes_worked - self.normal_minutes_per_session, 0)

    @property
    def total_time_worked_minutes(self) -> int:
        if not self.clock_in or not self.clock_out:
            return 0  # Handle missing clock in/out times
        # Calculate the difference in time
        delta: timedelta = self.clock_out - self.clock_in
        seconds_to_minutes: int = int(delta.total_seconds() // 60)
        return seconds_to_minutes

    def day_and_date_clocked_in(self) -> str:
        """
            **day_and_date_clocked_in**
            Returns the day of the week and the exact date worked in the format "Monday, 22 June 2025".
            Returns:
                str: Day of the week and date worked.
        """
        day_of_week = self.clock_in.strftime("%A")
        date_worked = self.clock_in.strftime("%d %B %Y")
        return f"{day_of_week}, {date_worked}"

    def day_and_date_clocked_out(self) -> str:
        """
            Returns the day of the week and the exact date worked in the format "Monday, 22 June 2025".
            Returns:
                str: Day of the week and date worked.
        """
        day_of_week = self.clock_out.strftime("%A")
        date_worked = self.clock_out.strftime("%d %B %Y")
        return f"{day_of_week}, {date_worked}"

TypeEMployeeDetails = TypeVar('EmployeeDetails')
TypeWorkSummary = TypeVar('WorkSummary')
TypePaySlip = TypeVar("Payslip")
TypeSalary = TypeVar("Salary")
class AttendanceSummary(BaseModel):
    attendance_id: str = Field(default_factory=create_id)
    employee_id: str
    name: str
    records: list[TimeRecord] | None
    employee: TypeEMployeeDetails | None
    work_summary: TypeWorkSummary | None

    def total_time_worked_minutes(self, from_date: date | None = None, to_date: date | None = None) -> int:
        """
        Calculates the total minutes worked by summing up the minutes worked from all records within the specified date range.

        Args:
            from_date (Optional[date]): The start date for the range. Defaults to None.
            to_date (Optional[date]): The end date for the range. Defaults to None.

        Returns:
            int: Total minutes worked.
        """

        def is_within_date_range(record: TimeRecord):
            return (not from_date or record.clock_in.date() >= from_date) and (
                    not to_date or record.clock_out.date() <= to_date)

        return sum(record.total_time_worked_minutes for record in self.records or [] if is_within_date_range(record))

    def normal_time_worked_minutes(self, from_date: date | None = None, to_date: date | None = None) -> int:
        """
        Calculates the total minutes worked by summing up the minutes worked from all records within the specified date range.

        Args:
            from_date (Optional[date]): The start date for the range. Defaults to None.
            to_date (Optional[date]): The end date for the range. Defaults to None.

        Returns:
            int: Total minutes worked.
        """

        def is_within_date_range(record: TimeRecord):
            return (not from_date or record.clock_in.date() >= from_date) and (
                    not to_date or record.clock_out.date() <= to_date)

        return sum(record.normal_minutes_worked for record in self.records or [] if is_within_date_range(record))

    def overtime_worked_minutes(self, from_date: date | None = None, to_date: date | None = None) -> int:
        """
        Calculates the total minutes worked by summing up the minutes worked from all records within the specified date range.

        Args:
            from_date (Optional[date]): The start date for the range. Defaults to None.
            to_date (Optional[date]): The end date for the range. Defaults to None.

        Returns:
            int: Total minutes worked.
        """

        def is_within_date_range(record: TimeRecord):
            return (not from_date or record.clock_in.date() >= from_date) and (
                    not to_date or record.clock_out.date() <= to_date)

        return sum(record.overtime_worked for record in self.records or [] if is_within_date_range(record))

    @property
    def has_clocked_in_today(self) -> bool:
        """
        Determines if the employee has clocked in today.

        Returns:
            bool: True if the employee has clocked in today, False otherwise.
        """
        today = datetime.now().date()
        return any(True for record in self.records
                   if (record.clock_in.date() == today) and not record.clock_out)

    @property
    def has_clocked_out_today(self) -> bool:
        """
        Determines if the employee has clocked out today.

        Returns:
            bool: True if the employee has clocked out today, False otherwise.
        """
        today = datetime.now().date()
        yesterday = today - relativedelta(day=1)

        def has_clocked(record):
            if not record.clock_in:
                return False
            if not record.clock_out:
                return False
            if (record.clock_in.date() != today) and (record.clock_in != yesterday):
                return False
            if record.clock_out.date() == today:
                return True
            return False

        return any(True for record in self.records if has_clocked(record=record))


class WorkSummary(BaseModel):
    work_id: str = Field(default_factory=create_id)
    attendance_id: str | None
    payslip_id: str | None
    employee_id: str

    normal_sign_in_hour: int = Field(default=7)
    normal_sign_off_hour: int = Field(default=17)

    normal_minutes_per_week: int = Field(default=40 * 60)

    normal_weeks_in_month: int = Field(default=4)
    normal_overtime_multiplier: float = Field(default=1.5)
    attendance: AttendanceSummary | None
    employee: TypeEMployeeDetails | None
    payslip: TypePaySlip | None
    salary: TypeSalary | None

    @property
    def period_start(self):
        if not self.payslip:
            return datetime.now().date().replace(day=1)
        return self.payslip.pay_period_start

    @property
    def period_end(self):
        if not self.payslip:
            period_start = self.period_start
            next_month = period_start + relativedelta(month=1)
            return next_month - relativedelta(day=1)

    @property
    def weeks_in_period(self) -> float:
        """
            Calculates the number of weeks_in_period between period_start and period_end.
        Returns:
            float: Number of weeks_in_period.
        """
        delta = (self.payslip.pay_period_start - self.payslip.pay_period_end).days
        return delta / 7

    def overtime_rate_cents_per_minute(self) -> float:
        """
            **overtime_rate_cents_per_minute**
                its basically normal rate increased by normal_overtime_multiplier
        """
        return self.normal_rate_cents_per_minute * self.normal_overtime_multiplier

    @property
    def normal_rate_cents_per_minute(self) -> float:
        """Amount of Money made in cents per minute when normal time is worked"""
        if not self.salary:
            return 0
        return self.salary.amount_in_cents / (self.normal_minutes_per_week * self.normal_weeks_in_month)

    @property
    def total_minutes_worked(self) -> int:
        """absolute total of minutes worked per period"""
        if self.payslip.pay_period_start is None or self.payslip.pay_period_end is None:
            return 0

        return sum(
            summary.total_time_worked_minutes(from_date=self.payslip.pay_period_start,
                                              to_date=self.payslip.pay_period_end) for summary in
            self.attendance)

    @property
    def overtime_worked_minutes(self) -> int:
        """
        **overtime_worked_minutes**
            Calculates the total overtime minutes worked for the employee within the specified period.

        Note Overtime will not be paid if total minutes worked is less than normal time expected to be worked in the month

        Returns:
            int: Total overtime minutes worked.
        """
        if self.total_minutes_worked < (self.normal_minutes_per_week * self.weeks_in_period):
            return 0

        return sum(summary.overtime_worked_minutes(from_date=self.payslip.pay_period_start,
                                                   to_date=self.payslip.pay_period_end) for summary in
                   self.attendance)

    @property
    def normal_time_worked_minutes(self) -> int:
        """
        Calculates the total overtime minutes worked for the employee within the specified period.

        Returns:
            int: Total overtime minutes worked.
        """
        if self.payslip.pay_period_start is None or self.payslip.pay_period_end is None:
            return 0

        return sum(
            summary.normal_time_worked_minutes(from_date=self.payslip.pay_period_start,
                                               to_date=self.payslip.pay_period_end) for summary in
            self.attendance)

    @property
    def overtime_in_cents(self) -> int:
        """
            **actual_overtime_cents**
            Calculates the total overtime pay for the employee within the specified period.

            Returns:
                int: Total overtime pay.
        """
        return int(self.overtime_worked_minutes * self.overtime_rate_cents_per_minute())

    @property
    def normal_pay_cents(self) -> int:
        """
            **normal_pay_cents**
        :return:
        """
        return int(self.normal_time_worked_minutes * self.normal_rate_cents_per_minute)

    @property
    def net_salary_cents(self) -> int:
        """
        **actual_salary_cents**
            Calculates the total salary for the employee within the specified period, including overtime pay.
            Returns:
                int: Total salary.
        """
        return self.overtime_in_cents + self.normal_pay_cents


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
    email: EmailStr
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
    attendance_register: AttendanceSummary | None
    work_summary: WorkSummary | None
    payslip: list["Payslip"] = Field(default_factory=list)

    @property
    def display_names(self) -> str:
        return f"{self.full_names} {self.last_name}"


class Salary(BaseModel):
    salary_id: str = Field(default_factory=create_id)
    employee_id: str
    company_id: str
    branch_id: str
    amount: int
    pay_day: int

    @property
    def effective_pay_date(self) -> date:
        """
        Calculate the effective pay date for the current month.
        Adjust the date if the pay_day falls on a weekend.
        :return: The effective pay date as a datetime.date object.
        """
        today = datetime.today()
        effective_date = datetime(today.year, today.month, self.pay_day)

        if effective_date.weekday() == 5:  # Saturday
            effective_date -= timedelta(days=1)
        elif effective_date.weekday() == 6:  # Sunday
            effective_date += timedelta(days=1)

        return effective_date.date()

    @property
    def next_month_pay_date(self) -> date:
        """
        Calculate the effective pay date for the next month.
        Adjust the date if the pay_day falls on a weekend.
        :return: The effective pay date for the next month as a datetime.date object.
        """
        next_month_effective_date = self.effective_pay_date + relativedelta(months=1)

        if next_month_effective_date.weekday() == 5:  # Saturday
            next_month_effective_date -= timedelta(days=1)
        elif next_month_effective_date.weekday() == 6:  # Sunday
            next_month_effective_date += timedelta(days=1)

        return next_month_effective_date

    @property
    def amount_in_cents(self) -> int:
        """converts salary amount which is in rands to cents"""
        return int(self.amount * 100)


class Deductions(BaseModel):
    deduction_id: str
    payslip_id: str
    amount_in_cents: int
    reason: str


class BonusPay(BaseModel):
    bonus_id: str
    payslip_id: str
    amount_in_cents: int
    reason: str


def pay_period_start() -> date:
    return datetime.now().date().replace(day=1)


def pay_period_end() -> date:
    next_month = pay_period_start() + relativedelta(month=1)
    return next_month - relativedelta(day=1)


class Payslip(BaseModel):
    payslip_id: str = Field(default_factory=create_id)
    employee_id: str
    salary_id: str
    pay_period_start: date = Field(default_factory=pay_period_start)
    pay_period_end: date = Field(default_factory=pay_period_end)

    employee: EmployeeDetails | None
    salary: Salary | None

    applied_deductions: list[Deductions] | None
    bonus_pay: list[BonusPay] | None
    work_sheets: WorkSummary | None

    @property
    def month_of(self):
        # Return the name of the month
        return calendar.month_name[self.pay_period_start.month]

    @property
    def total_bonus(self) -> int:
        return sum(bonus.amount_in_cents for bonus in self.bonus_pay)

    @property
    def total_deductions(self) -> int:
        return sum(deduct.amount_in_cents for deduct in self.applied_deductions)

    @property
    def net_salary(self) -> int:
        return int(self.work_sheets.net_salary_cents/100)


class WorkOrder(BaseModel):
    order_id: str = Field(default_factory=create_id)

    job_title: str
    description: str
    assigned_roles: list[str]

    job_scheduled_start_time: datetime
    job_scheduled_time_completion: datetime

    work_address_id: str
    contact_person_name: str
    contact_person_contact_id: str

    @property
    def total_scheduled_work_minutes(self) -> int:
        return int((self.job_scheduled_time_completion - self.job_scheduled_start_time).total_seconds() * 60)


EmployeeDetails.update_forward_refs()
WorkSummary.update_forward_refs()
AttendanceSummary.update_forward_refs()
