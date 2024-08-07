from datetime import datetime

from flask import Flask
from sqlalchemy.orm import joinedload

from src.controller import Controllers, error_handler
from src.database.models.companies import EmployeeRoles, EmployeeDetails, AttendanceSummary, TimeRecord, Salary
from src.database.sql.companies import EmployeeORM, AttendanceSummaryORM, TimeRecordORM, SalaryORM
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

    @error_handler
    async def get_employee_complete_details_uid(self, uid: str) -> EmployeeDetails | None:
        """
        Get complete details of an employee by UID, including attendance summaries and time records.

        :param uid: UID of the employee
        :return: EmployeeDetails instance or None
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM = session.query(EmployeeORM).filter_by(uid=uid).options(
                joinedload(EmployeeORM.attendance_register).joinedload(AttendanceSummaryORM.records)
            ).first()

            if isinstance(employee_orm, EmployeeORM):
                return EmployeeDetails(**employee_orm.to_dict(include_relationships=True))

            return None

    @error_handler
    async def get_employee_complete_details_employee_id(self, employee_id: str) -> EmployeeDetails | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM | None = session.query(EmployeeORM).filter_by(employee_id=employee_id).options(
                joinedload(EmployeeORM.attendance_register).joinedload(AttendanceSummaryORM.records)
            ).one_or_none()

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
                self.logger.info("Already Signed IN")
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
            salary_orm = session.query(SalaryORM).filter_by(employee_id=salary.employee_id).first()
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
