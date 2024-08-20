from datetime import datetime, timedelta
import calendar

from flask import Flask
from pydantic import ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from src.controller import Controllers, error_handler
from src.database.models.companies import EmployeeRoles, EmployeeDetails, AttendanceSummary, TimeRecord, Salary, \
    WorkSummary, Payslip
from src.database.sql.companies import EmployeeORM, AttendanceSummaryORM, TimeRecordORM, SalaryORM, WorkSummaryORM, \
    PaySlipORM
from src.main import system_cache

cached_ttl = system_cache.cached_ttl


class EmployeesController(Controllers):
    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    @error_handler
    async def get_employee_attendance_register(self, employee_id: str) -> AttendanceSummary | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(employee_id=employee_id).first()
            if isinstance(attendance_register_orm, AttendanceSummaryORM):
                return AttendanceSummary(**attendance_register_orm.to_dict())
    async def add_update_attendance_register(self, attendance_register: AttendanceSummary) -> AttendanceSummary | None:
        """

        :param attendance_register:
        :return:
        """
        with self.get_session() as session:

            attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(
                employee_id=attendance_register.employee_id).first()

            if isinstance(attendance_register_orm, AttendanceSummaryORM):
                attendance_register_orm.attendance_id = attendance_register.attendance_id
                attendance_register_orm.name = attendance_register.name
            else:
                session.add(AttendanceSummaryORM(**attendance_register.dict(exclude={'records', 'employee', 'work_summary'})))

            return attendance_register

    @error_handler
    async def get_employee_complete_details_uid(self, uid: str) -> EmployeeDetails | None:
        """
        Get complete details of an employee by UID, including attendance summaries and time records.

        :param uid: UID of the employee
        :return: EmployeeDetails instance or None
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM | None = (
                session.query(EmployeeORM)
                .filter_by(uid=uid)
                .options(
                    joinedload(EmployeeORM.attendance_register)
                    .joinedload(AttendanceSummaryORM.records),
                    joinedload(EmployeeORM.work_summary),
                    joinedload(EmployeeORM.payslip)
                )
                .one_or_none()
            )

            if employee_orm:
                employee_data = employee_orm.to_dict(include_relationships=True)
                self.logger.info(f"Employee Details UID : {employee_data}")
                try:
                    employee_details = EmployeeDetails(**employee_data)
                    self.logger.info(f"Employee Details UID : {employee_details}")
                    return employee_details
                except Exception as e:
                    print(str(e))
            return None


    @error_handler
    async def get_employee_complete_details_employee_id(self, employee_id: str) -> EmployeeDetails | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM | None = (
                session.query(EmployeeORM)
                .filter_by(employee_id=employee_id)
                .options(
                    joinedload(EmployeeORM.attendance_register)
                    .joinedload(AttendanceSummaryORM.records),
                    joinedload(EmployeeORM.work_summary),
                    joinedload(EmployeeORM.payslip)
                )
                .one_or_none()
            )

            self.logger.info(f"GET EMPLOYEE DETAILS UID: {employee_orm.to_dict()}")

            if isinstance(employee_orm, EmployeeORM):
                return EmployeeDetails(**employee_orm.to_dict(include_relationships=True))

            return None

    @error_handler
    async def sign_in_employee(self, employee_detail: EmployeeDetails) -> bool:
        """
        Sign in an employee if they have not already signed in.

        :param employee_detail: Details of the employee to be signed in.
        :return: True if the employee was successfully signed in, False otherwise.
        """
        with self.get_session() as session:

            attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(
                employee_id=employee_detail.employee_id).first()
            if isinstance(attendance_register_orm, AttendanceSummaryORM):
                attendance_register = AttendanceSummary(**attendance_register_orm.to_dict(include_relationships=False))
            else:
                attendance_register = AttendanceSummary(employee_id=employee_detail.employee_id,
                                                        name=employee_detail.display_names)
                session.add(AttendanceSummaryORM(**attendance_register.dict(exclude={'records'})))

        with self.get_session() as session:
            # Check if there is an existing clock_in without a clock_out
            existing_record = session.query(TimeRecordORM).filter(
                TimeRecordORM.attendance_id == attendance_register.attendance_id,
                TimeRecordORM.clock_in.isnot(None),
                TimeRecordORM.clock_out.is_(None)
            ).first()

            if existing_record:
                # Employee already signed in
                return False

            # Create new time record for clock in
            time_record = TimeRecord(attendance_id=attendance_register.attendance_id, clock_in=datetime.now())
            session.add(TimeRecordORM(**time_record.dict()))

        self.logger.info("Successfully Signed In")

        return True

    @error_handler
    async def sign_out_employee(self, employee_detail: EmployeeDetails) -> bool:
        """
        Sign out an employee if they are currently signed in.

        :param employee_detail: Details of the employee to be signed out.
        :return: True if the employee was successfully signed out, False otherwise.
        """
        with self.get_session() as session:
            attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(
                employee_id=employee_detail.employee_id).first()

            if not isinstance(attendance_register_orm, AttendanceSummaryORM):
                self.logger.info("Attendance Register not found")
                return False

            attendance_register = AttendanceSummary(**attendance_register_orm.to_dict(include_relationships=False))

            # Check if there is an existing clock_in without a clock_out
            existing_record = session.query(TimeRecordORM).filter(
                TimeRecordORM.attendance_id == attendance_register.attendance_id,
                TimeRecordORM.clock_in.isnot(None),
                TimeRecordORM.clock_out.is_(None)
            ).first()

            if not existing_record:
                # Employee not signed in
                self.logger.info("Not Signed IN")
                return False

            # Update the existing time record with clock out time
            existing_record.clock_out = datetime.now()

        self.logger.info("Successfully Signed Out")

        return True

    @staticmethod
    async def get_roles() -> list[str]:
        return EmployeeRoles.get_all_roles()

    # noinspection DuplicatedCode
    @error_handler
    async def add_update_employee_details(self, employee_details: EmployeeDetails):
        """

        :param employee_details:
        :return:
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM = session.query(EmployeeORM).filter_by(
                uid=employee_details.uid).first()

            await system_cache.clear_mem_cache()

            if isinstance(employee_orm, EmployeeORM):
                employee_orm.branch_id = employee_details.branch_id
                employee_orm.company_id = employee_details.company_id
                employee_orm.full_names = employee_details.full_names
                employee_orm.last_name = employee_details.last_name
                employee_orm.id_number = employee_details.id_number
                employee_orm.email = employee_details.email
                employee_orm.contact_number = employee_details.contact_number
                employee_orm.position = employee_details.position
                employee_orm.role = employee_details.role
                employee_orm.date_of_birth = employee_details.date_of_birth
                employee_orm.date_joined = employee_details.date_joined
                employee_orm.salary = employee_details.salary
                employee_orm.is_active = employee_details.is_active

                if employee_details.address_id:
                    employee_orm.address_id = employee_details.address_id
                if employee_details.contact_id:
                    employee_orm.contact_id = employee_details.contact_id
                if employee_details.postal_id:
                    employee_orm.postal_id = employee_details.postal_id
                if employee_details.bank_account_id:
                    employee_orm.bank_account_id = employee_details.bank_account_id

            else:
                session.add(EmployeeORM(**employee_details.dict(exclude={'attendance_register'})))

            return employee_details

    @error_handler
    async def add_update_employee_salary(self, salary: Salary) -> Salary | None:
        """
            **add_update_employee_salary**
        :return:
        """
        with self.get_session() as session:
            salary_orm: SalaryORM = session.query(SalaryORM).filter_by(employee_id=salary.employee_id).first()
            if isinstance(salary_orm, SalaryORM):
                salary_orm.salary_id = salary.salary_id
                salary.company_id = salary.company_id
                salary.branch_id = salary.branch_id
                salary_orm.amount = salary.amount
                salary_orm.pay_day = salary.pay_day
                salary_orm.effective_date = salary.effective_pay_date
                return salary
            session.add(SalaryORM(**salary.dict(), effective_date=salary.effective_pay_date))

            return salary

    @error_handler
    async def get_salary_details(self, employee_id: str) -> Salary | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            salary_orm = session.query(SalaryORM).filter_by(employee_id=employee_id).first()
            if isinstance(salary_orm, SalaryORM):
                return Salary(**salary_orm.to_dict())
            return None

    async def create_employee_payslip(self, payslip: Payslip) -> Payslip | None:
        """

        :param payslip:
        :return:
        """
        with self.get_session() as session:
            session.add(PaySlipORM(**payslip.dict(exclude={'employee', 'salary', 'applied_deductions', 'bonus_pay',
                                                           'work_sheets'})))
            return payslip

    async def get_present_employee_payslip(self, employee_id: str) -> Payslip | None:
        """
        Get the latest payslip for the specified employee.

        :param employee_id: The ID of the employee whose payslip is being retrieved.
        :return: The latest PayslipORM instance or None if no payslip is found.
        """
        with self.get_session() as session:
            payslip_orm: PaySlipORM = session.query(PaySlipORM).filter_by(employee_id=employee_id).order_by(
                desc(PaySlipORM.pay_period_end)
            ).first()
            if not isinstance(payslip_orm, PaySlipORM):
                return None

            this_month = datetime.now().month
            payslip = Payslip(**payslip_orm.to_dict(include_relationships=False))
            if (payslip.pay_period_end.month == this_month) or (payslip.pay_period_start.month == this_month):
                return payslip
        return None

    async def get_employee_complete_work_summary(self, employee_id: str) -> list[WorkSummary]:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            work_summary_orm_list = session.query(WorkSummaryORM).filter_by(employee_id=employee_id).all()
            return [work.to_dict(include_relationships=False) for work in work_summary_orm_list or []
                    if isinstance(work, WorkSummaryORM)]

    async def get_employee_current_work_summary(self, employee_id: str) -> WorkSummary | None:
        """
        Retrieves the current work summary for the given employee based on the start date of the current month.

        :param employee_id: The ID of the employee.
        :return: A WorkSummary instance representing the current work summary, or None if not found.
        """
        start_of_this_month = datetime.now().date().replace(day=1)
        self.logger.info(f"Current Work Summary Start Date: {start_of_this_month}")

        with self.get_session() as session:
            work_summary_orm = session.query(WorkSummaryORM).filter_by(
                employee_id=employee_id,
                period_start=start_of_this_month
            ).one_or_none()
            return WorkSummary(**work_summary_orm.to_dict(include_relationships=False)) if work_summary_orm else None


    async def add_update_current_work_summary(self, work_summary: WorkSummary) -> WorkSummary | None:
        """

        :param work_summary:
        :return:
        """
        with self.get_session() as session:
            work_summary_orm = session.query(WorkSummaryORM).filter_by(work_id=work_summary.work_id).first()
            if isinstance(work_summary_orm, WorkSummaryORM):
                work_summary_orm.attendance_id = work_summary.attendance_id
                work_summary_orm.payslip_id = work_summary.payslip_id
                work_summary_orm.employee_id = work_summary.employee_id
                work_summary_orm.normal_minutes_per_week = work_summary.normal_minutes_per_week
                work_summary_orm.normal_sign_in_hour = work_summary.normal_sign_in_hour
                work_summary_orm.normal_sign_off_hour = work_summary.normal_sign_off_hour
                work_summary_orm.normal_weeks_in_month = work_summary.normal_weeks_in_month
                work_summary_orm.normal_overtime_multiplier = work_summary.normal_overtime_multiplier
                work_summary_orm.period_start = work_summary.period_start
                work_summary_orm.period_end = work_summary.period_end

            else:
                work_summary_orm = WorkSummaryORM(**work_summary.dict(exclude={'attendance', 'employee',
                                                                               'payslip', 'salary'}),
                                                  period_start=work_summary.period_start, period_end=work_summary.period_end)
                session.add(work_summary_orm)

            return work_summary

    async def get_employee_last_month_work_summary(self, employee_id: str) -> WorkSummary | None:
        """
        Retrieves the work summary for the previous month.

        :param employee_id: The ID of the employee.
        :return: The work summary of the employee for the last month, or None if not found.
        """
        with self.get_session() as session:
            # Calculate the start date of the current month
            start_of_this_month = datetime.now().date().replace(day=1)

            # Calculate the start date of the previous month
            last_month = start_of_this_month - timedelta(days=1)
            start_of_last_month = last_month.replace(day=1)

            self.logger.info(f"Last Month Work Summary Start Date: {start_of_last_month}")

            # Query the work summary for the last month
            work_summary_orm = session.query(WorkSummaryORM).filter_by(employee_id=employee_id,
                                                                       period_start=start_of_last_month).first()

            return WorkSummary(**work_summary_orm.to_dict()) if isinstance(work_summary_orm, WorkSummaryORM) else None


    async def get_complete_employee_details_for_company(self, company_id: str) -> list[EmployeeDetails]:
        """

        :param company_id:
        :return:
        """
        with self.get_session() as session:
            company_employees = session.query(EmployeeORM).filter_by(company_id=company_id).options(
                joinedload(EmployeeORM.attendance_register),
                joinedload(EmployeeORM.work_summary),
                joinedload(EmployeeORM.payslip)
            ).all()

            return [EmployeeDetails(**employee.to_dict(include_relationships=True)) for employee in company_employees or []
                    if isinstance(employee, EmployeeORM)]
