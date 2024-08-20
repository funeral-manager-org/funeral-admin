from __future__ import annotations
import calendar
from datetime import datetime, date, timedelta
from typing import Optional, ForwardRef

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, EmailStr, conint, field_validator

from src.database.constants import NAME_LEN
from src.database.models import ID_LEN, CK_LEN, MIN_NAME_LEN, MAX_CLIENTS, MAX_EMPLOYEES, MIN_SALARY, MAX_SALARY
from src.utils import create_id, string_today, create_plan_number, create_employee_id


class Company(BaseModel):
    company_id: str = Field(default_factory=create_id, max_length=ID_LEN)
    admin_uid: str = Field(max_length=ID_LEN)
    reg_ck: str = Field(min_length=CK_LEN, max_length=CK_LEN)
    vat_number: str | None = Field(default=None, min_length=10, max_length=16)
    company_name: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    company_description: str = Field(min_length=MIN_NAME_LEN, max_length=255)
    company_slogan: str = Field(min_length=MIN_NAME_LEN, max_length=255)
    date_registered: str = Field(default_factory=string_today, min_length=10, max_length=19)
    total_users: conint(ge=0, le=MAX_EMPLOYEES) = Field(default=0)
    total_clients: conint(ge=0, le=MAX_CLIENTS) = Field(default=0)


class CompanyBranches(BaseModel):
    """

    """
    branch_id: str = Field(default_factory=create_id, min_length=ID_LEN, max_length=ID_LEN)
    company_id: str = Field(max_length=ID_LEN)
    branch_name: str = Field(min_length=4, max_length=NAME_LEN)
    branch_description: str = Field(min_length=4, max_length=255)
    date_registered: str = Field(default_factory=string_today, min_length=10, max_length=16)
    total_clients: conint(ge=0, le=MAX_CLIENTS) = Field(default=0, ge=0)
    total_employees: conint(ge=0, le=MAX_EMPLOYEES) = Field(default=0, ge=0)

    address_id: str | None = Field(default=None)
    contact_id: str | None = Field(default=None)
    postal_id: str | None = Field(default=None)
    bank_account_id: str | None = Field(default=None)


class PlanTypes(BaseModel):
    """
        User defined model to allow managers to create their own plan types
    """
    branch_id: str = Field(max_length=ID_LEN)
    company_id: str = Field(max_length=ID_LEN)

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
    company_id: str | None = Field(default=None)

    plan_number: str = Field(default_factory=create_plan_number)
    plan_name: str = Field(min_length=MIN_NAME_LEN, max_length=255)
    plan_type: str = Field(min_length=MIN_NAME_LEN, max_length=255)

    benefits: str = Field(min_length=MIN_NAME_LEN, max_length=255 * 5)
    coverage_amount: conint(ge=0, le=5_000_000)
    premium_costs: conint(ge=0, le=5_000_000)
    additional_details: str = Field(min_length=MIN_NAME_LEN, max_length=255 * 5)
    terms_and_conditions: str = Field(min_length=MIN_NAME_LEN, max_length=255 * 36)
    inclusions: str = Field(min_length=MIN_NAME_LEN, max_length=255 * 5)
    exclusions: str = Field(min_length=MIN_NAME_LEN, max_length=255 * 5)
    contact_information: str = Field(min_length=MIN_NAME_LEN, max_length=16)


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


# noinspection PyMethodParameters



class Salary(BaseModel):
    salary_id: str = Field(default_factory=create_id)
    employee_id: str = Field(max_length=ID_LEN)
    company_id: str = Field(max_length=ID_LEN)
    branch_id: str = Field(max_length=ID_LEN)
    amount: conint(ge=MIN_SALARY, le=MAX_SALARY)
    pay_day: conint(ge=1, le=31)

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
    """cannot deduct more than 2500"""
    deduction_id: str = Field(default_factory=create_id)
    payslip_id: str = Field(max_length=ID_LEN)
    amount_in_cents: conint(ge=0, le=2_500_00) = Field(default=0)
    reason: str| None = Field(min_length=12, max_length=255 * 10)

    @property
    def amount(self):
        return int(self.amount_in_cents / 100)


class BonusPay(BaseModel):
    bonus_id: str = Field(default_factory=create_id)
    payslip_id: str = Field(max_length=ID_LEN)
    amount_in_cents: conint(ge=0, le=50_000_00) = Field(default=0)
    reason: str| None = Field(min_length=12, max_length=255 * 10)

    @property
    def amount(self):
        return int(self.amount_in_cents / 100)


def pay_period_start() -> date:
    return datetime.now().date().replace(day=1)


def pay_period_end() -> date:
    return datetime.now().date().replace(day=1) + relativedelta(months=1) - relativedelta(days=1)


class Payslip(BaseModel):
    payslip_id: str = Field(default_factory=create_id)
    employee_id: str = Field(max_length=ID_LEN)
    salary_id: str = Field(max_length=ID_LEN)
    pay_period_start: date = Field(default_factory=pay_period_start)
    pay_period_end: date = Field(default_factory=pay_period_end)

    employee: EmployeeDetails | None = Field(default=None)
    salary: Salary | None = Field(default=None)

    applied_deductions: list[Deductions] | None = Field(default_factory=list)
    bonus_pay: list[BonusPay] | None = Field(default_factory=list)
    work_sheets: WorkSummary | None = Field(default=None)

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
        return int(self.work_sheets.net_salary_cents / 100)


class TimeRecord(BaseModel):
    time_id: str = Field(default_factory=create_id, max_length=ID_LEN)
    attendance_id: str = Field(max_length=ID_LEN)
    normal_minutes_per_session: conint(ge=480, le=960) = Field(default=8 * 60)
    clock_in: datetime
    clock_out: datetime | None = Field(default=None)

    # @field_validator('clock_in')
    # def validate_clock_in(cls, v):
    #     # Adjust the timedelta values as needed
    #     min_allowed_date = datetime.now() - timedelta(days=7)  # 7 days in the past
    #     max_allowed_date = datetime.now() + timedelta(days=1)  # One day in the future
    #
    #     if v < min_allowed_date or v > max_allowed_date:
    #         raise ValueError('Clock in time must be within a reasonable range')
    #     return v
    #
    # @field_validator('clock_out')
    # def validate_clock_out(cls, v, values):
    #     try:
    #         if v and v >= values['clock_in']:
    #             raise ValueError('Clock out time must be after clock in time')
    #     except Exception as e:
    #         raise ValueError('Clock out time must be after clock in time')
    #     return v

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


class AttendanceSummary(BaseModel):
    attendance_id: str = Field(default_factory=create_id)
    employee_id: str = Field(max_length=ID_LEN)
    name: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    records: list[TimeRecord] = Field(default_factory=list)
    employee: Optional[ForwardRef("EmployeeDetails", is_class=True)] = Field(default=None)
    work_summary: Optional[ForwardRef("WorkSummary", is_class=True)] = Field(default=None)

    def total_time_worked_minutes(self, from_date: date | None = None, to_date: date | None = None) -> int:
        """
        Calculates the total minutes worked by summing up the minutes worked from all records within the
        specified date range.

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
        Calculates the total minutes worked by summing up the minutes worked from all
        records within the specified date range.

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
        Calculates the total minutes worked by summing up the minutes worked
        from all records within the specified  date range.

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
    work_id: str = Field(default_factory=create_id,  max_length=ID_LEN)
    attendance_id: str | None = Field(default=None, max_length=ID_LEN)
    payslip_id: str | None = Field(default=None, max_length=ID_LEN)
    employee_id: str = Field(max_length=ID_LEN)

    normal_sign_in_hour: conint(ge=0, le=23) = Field(default=7)
    normal_sign_off_hour: conint(ge=10, le=23) = Field(default=17)

    normal_minutes_per_week: conint(ge=2400, le=5040) = Field(default=40 * 60)

    normal_weeks_in_month: conint(ge=4, le=5) = Field(default=4)
    normal_overtime_multiplier: float = Field(default=1.5)
    attendance: Optional[AttendanceSummary] = Field(default=None)
    employee: Optional[ForwardRef("EmployeeDetails", is_class=True)] = Field(default=None)
    payslip: Optional[Payslip] = Field(default=None)
    salary: Optional[Salary] = Field(default=None)

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
        if not (self.payslip.pay_period_start and self.payslip.pay_period_end):
            return 4

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

        Note Overtime will not be paid if total minutes worked is less than normal time expected to
        be worked in the month

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

    uid: str | None = Field(default=None)
    company_id: str | None = Field(default=None)
    branch_id: str | None = Field(default=None)

    full_names: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    last_name: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    id_number: str = Field(min_length=13, max_length=13)
    email: EmailStr
    contact_number: str = Field(min_length=10, max_length=16)
    position: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    role: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    date_of_birth: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    date_joined: str = Field(default_factory=string_today)
    salary: conint(ge=MIN_SALARY, le=MAX_SALARY)
    is_active: bool = Field(default=True)

    address_id: str | None = Field(default=None)
    contact_id: str | None = Field(default=None)
    postal_id: str | None = Field(default=None)
    bank_account_id: str | None = Field(default=None)
    attendance_register: AttendanceSummary | None = Field(default=None)
    work_summary: WorkSummary | None = Field(default=None)
    payslip: list[Payslip] = Field(default_factory=list)

    @property
    def display_names(self) -> str:
        return f"{self.full_names} {self.last_name}"


# noinspection PyMethodParameters
class WorkOrder(BaseModel):
    order_id: str = Field(default_factory=create_id)

    job_title: str = Field(min_length=MIN_NAME_LEN, max_length=NAME_LEN)
    description: str = Field(min_length=MIN_NAME_LEN, max_length=255)
    assigned_roles: list[str] = Field(max_items=5)

    job_scheduled_start_time: datetime
    job_scheduled_time_completion: datetime

    work_address_id: str
    contact_person_name: str
    contact_person_contact_id: str

    @field_validator('job_scheduled_start_time')
    def validate_start_time(cls, v):
        min_allowed_start_time = datetime.now() + timedelta(hours=1)
        if v < min_allowed_start_time:
            raise ValueError("Job scheduled start time must be at least one hour in the future")
        return v

    @field_validator('job_scheduled_time_completion')
    def validate_completion_time(cls, v, values):
        if v <= values['job_scheduled_start_time']:
            raise ValueError("Job scheduled completion time must be after start time")

        # Add a check for minimum job duration here if needed
        # For example:
        min_job_duration = timedelta(hours=1)
        if v - values['job_scheduled_start_time'] < min_job_duration:
            raise ValueError("Job duration must be at least one hour")

        return v

    @property
    def total_scheduled_work_minutes(self) -> int:
        return int((self.job_scheduled_time_completion - self.job_scheduled_start_time).total_seconds() * 60)


Payslip.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)
TimeRecord.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)
AttendanceSummary.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)
WorkSummary.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)
EmployeeDetails.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)
WorkOrder.model_rebuild(raise_errors=False, force=True, _parent_namespace_depth=4)

