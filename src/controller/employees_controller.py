from datetime import datetime

from flask import Flask
from sqlalchemy.orm import joinedload

from src.controller import Controllers, error_handler
from src.database.models.bank_accounts import BankAccount
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails, CoverPlanDetails, \
    AttendanceSummary, TimeRecord
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation, PaymentMethods, InsuredParty
from src.database.sql.bank_account import BankAccountORM
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM, CoverPlanDetailsORM, \
    AttendanceSummaryORM, TimeRecordORM
from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
from src.database.sql.covers import PolicyRegistrationDataORM, ClientPersonalInformationORM
from src.main import system_cache

cached_ttl = system_cache.cached_ttl


class EmployeesController(Controllers):
    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def get_employee_attendance_register(self, employee_id: str) -> AttendanceSummary | None:
        """

        :param employee_id:
        :return:
        """
        with self.get_session() as session:
            attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(employee_id=employee_id).first()
            if isinstance(attendance_register_orm, AttendanceSummaryORM):
                return AttendanceSummary(**attendance_register_orm.to_dict())

    async def get_employee_complete_details_uid(self, uid: str) -> EmployeeDetails | None:
        """
        Get complete details of an employee by UID, including attendance summaries and time records.

        :param uid: UID of the employee
        :return: EmployeeDetails instance or None
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM = session.query(EmployeeORM).filter_by(uid=uid).options(
                joinedload(EmployeeORM.attendance_register).joinedload(AttendanceSummaryORM.records)
            ).one_or_none()

            if isinstance(employee_orm, EmployeeORM):
                return EmployeeDetails(**employee_orm.to_dict(include_relationships=True))
            return None

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
            :param employee_detail:
            :return:
        """

        if employee_detail.attendance_register is None:

            attendance_register = AttendanceSummary(employee_id=employee_detail.employee_id,
                                                    name=employee_detail.display_names)
            with self.get_session() as session:
                session.add(AttendanceSummaryORM(**attendance_register.dict(exclude={'records'})))
                session.flush()

            time_record = TimeRecord(attendance_id=attendance_register.attendance_id, clock_in=datetime.now())

            with self.get_session() as session:
                session.add(TimeRecordORM(**time_record.dict(exclude={'summary'})))

            return True
        else:
            with self.get_session() as session:
                attendance_register_orm = session.query(AttendanceSummaryORM).filter_by(
                    employee_id=employee_detail.employee_id)

                if isinstance(attendance_register_orm, AttendanceSummaryORM):
                    time_record = TimeRecord(attendance_id=attendance_register_orm.attendance_id,
                                             clock_in=datetime.now())
                    session.add(TimeRecordORM(**time_record.dict(exclude={'summary'})))
            return True
        return False

    async def get_roles(self) -> list[str]:
        return EmployeeRoles.get_all_roles()

    async def add_update_employee_details(self, employee_details: EmployeeDetails):
        """

        :param employee_details:
        :return:
        """
        with self.get_session() as session:
            employee_orm: EmployeeORM = session.query(EmployeeORM).filter_by(
                uid=employee_details.uid).first()

            if isinstance(employee_orm, EmployeeORM):
                employee_orm.uid = employee_details.uid
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
            else:
                session.add(EmployeeORM(**employee_details.dict(exclude={'attendance_register'})))
