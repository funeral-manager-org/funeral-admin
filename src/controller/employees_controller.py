from datetime import datetime

from flask import Flask
from sqlalchemy.orm import joinedload

from src.controller import Controllers, error_handler
from src.database.models.bank_accounts import BankAccount
from src.database.models.companies import Company, CompanyBranches, EmployeeRoles, EmployeeDetails, CoverPlanDetails, \
    AttendanceSummary
from src.database.models.contacts import Address, PostalAddress, Contacts
from src.database.models.covers import PolicyRegistrationData, ClientPersonalInformation, PaymentMethods, InsuredParty
from src.database.sql.bank_account import BankAccountORM
from src.database.sql.companies import CompanyORM, CompanyBranchesORM, EmployeeORM, CoverPlanDetailsORM, \
    AttendanceSummaryORM
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
