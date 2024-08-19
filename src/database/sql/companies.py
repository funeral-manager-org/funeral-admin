from datetime import datetime, date

from sqlalchemy import Column, String, inspect, Integer, Boolean, JSON, Date, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from src.database.constants import ID_LEN, NAME_LEN, SHORT_DESCRIPTION_lEN
from src.database.sql import Base, engine
from src.utils import string_today


class CompanyORM(Base):
    __tablename__ = "company"
    company_id: str = Column(String(ID_LEN), primary_key=True)
    admin_uid: str = Column(String(ID_LEN))
    reg_ck: str = Column(String(NAME_LEN))
    vat_number: str = Column(String(NAME_LEN), nullable=True)
    company_name: str = Column(String(NAME_LEN))
    company_description: str = Column(String(SHORT_DESCRIPTION_lEN))
    company_slogan: str = Column(String(SHORT_DESCRIPTION_lEN))
    date_registered: str = Column(String(NAME_LEN))
    total_users: int = Column(Integer)
    total_clients: int = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            "company_id": self.company_id,
            "admin_uid": self.admin_uid,
            "reg_ck": self.reg_ck,
            "vat_number": self.vat_number,
            "company_name": self.company_name,
            "company_description": self.company_description,
            "company_slogan": self.company_slogan,
            "date_registered": self.date_registered,
            "total_users": self.total_users,
            "total_clients": self.total_clients
        }


class CompanyBranchesORM(Base):
    __tablename__ = "company_branches"
    branch_id = Column(String(ID_LEN), primary_key=True, index=True)
    company_id = Column(String(ID_LEN), index=True)
    branch_name = Column(String(NAME_LEN))
    branch_description = Column(String(255))
    date_registered = Column(String(10), default=string_today)
    total_clients = Column(Integer, default=0)
    total_employees = Column(Integer, default=1)
    address_id = Column(String(ID_LEN), nullable=True, index=True)
    contact_id = Column(String(ID_LEN), nullable=True, index=True)
    postal_id = Column(String(ID_LEN), nullable=True, index=True)
    bank_account_id = Column(String(ID_LEN), nullable=True, index=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            "branch_id": self.branch_id,
            "company_id": self.company_id,
            "branch_name": self.branch_name,
            "branch_description": self.branch_description,
            "date_registered": self.date_registered,
            "total_clients": self.total_clients,
            "total_employees": self.total_employees,
            "address_id": self.address_id,
            "contact_id": self.contact_id,
            "postal_id": self.postal_id,
            "bank_account_id": self.bank_account_id

        }


class CoverPlanDetailsORM(Base):
    __tablename__ = "cover_plan_details"

    company_id = Column(String(NAME_LEN), index=True)

    plan_number = Column(String(10), primary_key=True, index=True)
    plan_name = Column(String(255))
    plan_type = Column(String(50))

    benefits = Column(Text)
    coverage_amount = Column(Integer)
    premium_costs = Column(Integer)
    additional_details = Column(String(1000))
    terms_and_conditions = Column(String(1000))
    inclusions = Column(Text)
    exclusions = Column(Text)
    contact_information = Column(String(255))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {

            "company_id": self.company_id,
            "plan_number": self.plan_number,
            "plan_name": self.plan_name,
            "plan_type": self.plan_type,
            "benefits": self.benefits,
            "coverage_amount": self.coverage_amount,
            "premium_costs": self.premium_costs,
            "additional_details": self.additional_details,
            "terms_and_conditions": self.terms_and_conditions,
            "inclusions": self.inclusions,
            "exclusions": self.exclusions,
            "contact_information": self.contact_information
        }


class EmployeeORM(Base):
    """Please Be very careful when loading this Class"""
    __tablename__ = "employee"
    employee_id = Column(String(9), primary_key=True, index=True)
    company_id = Column(String(ID_LEN), index=True)
    branch_id = Column(String(ID_LEN), index=True)

    uid = Column(String(ID_LEN), index=True)
    full_names = Column(String(255))
    last_name = Column(String(255))
    role = Column(String(36))
    id_number = Column(String(16))
    email = Column(String(255))
    contact_number = Column(String(20))
    position = Column(String(255))
    date_of_birth = Column(String(10))
    date_joined = Column(String(10))
    salary = Column(Integer)
    is_active = Column(Boolean, default=True)

    address_id = Column(String(ID_LEN), nullable=True, index=True)
    contact_id = Column(String(ID_LEN), nullable=True, index=True)
    postal_id = Column(String(ID_LEN), nullable=True, index=True)
    bank_account_id = Column(String(ID_LEN), nullable=True, index=True)

    attendance_register = relationship('AttendanceSummaryORM', back_populates='employee', lazy='joined',
                                       cascade="all, delete-orphan", uselist=False)

    work_summary = relationship('WorkSummaryORM', back_populates='employee', cascade='all, delete-orphan',
                                uselist=False)
    payslip = relationship('PaySlipORM', back_populates='employee', lazy=True, cascade='all, delete-orphan',
                           uselist=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships=False):
        """
        Convert the object to a dictionary representation.
        """

        def make_payslip(self) -> list[dict]:
            try:
                payslip_list = [payslip.to_dict(include_relationships=False) for payslip in self.payslip or []
                        if isinstance(payslip, PaySlipORM)]
            except Exception as e:
                print(str(e))
            return payslip_list

        return {
            "uid": self.uid,
            "employee_id": self.employee_id,
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "full_names": self.full_names,
            "last_name": self.last_name,
            "role": self.role,
            "id_number": self.id_number,
            "email": self.email,
            "contact_number": self.contact_number,
            "position": self.position,
            "date_of_birth": self.date_of_birth,
            "date_joined": self.date_joined,
            "salary": self.salary,
            "is_active": self.is_active,
            "address_id": self.address_id,
            "contact_id": self.contact_id,
            "postal_id": self.postal_id,
            "bank_account_id": self.bank_account_id,
            "attendance_register": self.attendance_register.to_dict(
                include_relationships=False) if include_relationships and self.attendance_register else None,
            "work_summary": self.work_summary.to_dict(
                include_relationships=False) if include_relationships and self.work_summary else None,
            "payslip": make_payslip(self=self) if include_relationships and self.payslip else []
        }




class SalaryORM(Base):
    __tablename__ = 'salaries'

    salary_id = Column(String(ID_LEN), primary_key=True, index=True)
    employee_id = Column(String(ID_LEN), ForeignKey('employee.employee_id'), index=True)
    company_id = Column(String(ID_LEN), index=True)
    branch_id = Column(String(ID_LEN), index=True)
    amount = Column(Integer)
    pay_day = Column(Integer)
    effective_date = Column(Date)
    payslip = relationship('PaySlipORM', back_populates='salary', lazy=True, uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships=False):
        """
        Convert the object to a dictionary representation.
        """
        return {
            'salary_id': self.salary_id,
            'employee_id': self.employee_id,
            'amount': self.amount,
            'pay_day': self.pay_day,
            'effective_date': str(self.effective_date),
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'payslip': self.payslip.to_dict(include_relationships=False) if self.payslip and include_relationships else None
        }


class SalaryPaymentORM(Base):
    __tablename__ = 'salary_payments'

    payment_id = Column(String(ID_LEN), primary_key=True, index=True)
    salary_id = Column(String(ID_LEN), index=True)
    payment_date = Column(Date)
    amount_paid = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            'payment_id': self.payment_id,
            'salary_id': self.salary_id,
            'payment_date': str(self.payment_date),
            'amount_paid': self.amount_paid
        }


class TimeRecordORM(Base):
    __tablename__ = "employee_time_record"
    time_id: str = Column(String(ID_LEN), primary_key=True, index=True)
    attendance_id: str = Column(String(ID_LEN), ForeignKey('employee_attendance_summary.attendance_id'))
    normal_minutes_per_session: int = Column(Integer, nullable=False)
    clock_in: datetime = Column(DateTime, index=True)
    clock_out: datetime = Column(DateTime, nullable=True)
    summary = relationship('AttendanceSummaryORM', back_populates='records', uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships: bool = False):
        """
        Convert the object to a dictionary representation.
        """
        return {
            'time_id': self.time_id,
            'attendance_id': self.attendance_id,
            'normal_minutes_per_session': self.normal_minutes_per_session,
            'clock_in': self.clock_in,
            'clock_out': self.clock_out,
            'summary': self.summary.to_dict(
                include_relationships=False) if include_relationships and self.summary else {}
        }


class AttendanceSummaryORM(Base):
    __tablename__ = "employee_attendance_summary"
    attendance_id: str = Column(String(ID_LEN), primary_key=True)
    employee_id: str = Column(String(ID_LEN), ForeignKey('employee.employee_id'))
    name: str = Column(String(NAME_LEN))
    records = relationship("TimeRecordORM", back_populates="summary", lazy=True, cascade="all, delete-orphan", uselist=True)
    employee = relationship("EmployeeORM", back_populates="attendance_register", uselist=False)
    work_summary = relationship('WorkSummaryORM', uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships: bool = False):
        """

        :param include_relationships:
        :return:
        """
        return {
            'attendance_id': self.attendance_id,
            'employee_id': self.employee_id,
            'name': self.name,
            'records': [record.to_dict(include_relationships=False) for record in self.records or []
                        if isinstance(record, TimeRecordORM)],
            'employee': self.employee.to_dict(include_relationships=False)
            if include_relationships and self.employee else None,
            'work_summary': self.work_summary.to_dict(include_relationships=False)
            if include_relationships and self.work_summary else None
        }


class WorkSummaryORM(Base):
    """

    """
    __tablename__ = "work_summary"

    work_id: str = Column(String(ID_LEN), primary_key=True)
    attendance_id: str = Column(String(ID_LEN), ForeignKey('employee_attendance_summary.attendance_id'))
    payslip_id: str = Column(String(ID_LEN), ForeignKey('payslip.payslip_id'))
    employee_id: str = Column(String(ID_LEN), ForeignKey('employee.employee_id'))

    period_start: date = Column(Date, index=True)
    period_end: date = Column(Date, index=True)

    normal_sign_in_hour: int = Column(Integer)
    normal_sign_off_hour: int = Column(Integer)

    normal_minutes_per_week: int = Column(Integer)

    normal_weeks_in_month: int = Column(Integer)
    normal_overtime_multiplier: int = Column(Float)

    attendance = relationship("AttendanceSummaryORM", back_populates="work_summary",
                              lazy=True, uselist=False)
    employee = relationship("EmployeeORM", back_populates="work_summary", uselist=False)
    payslip = relationship("PaySlipORM", back_populates="work_sheet", uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships: bool = False):
        """

        :param include_relationships:
        :return:
        """
        return {
            "work_id": self.work_id,
            "attendance_id": self.attendance_id,
            "payslip_id": self.payslip_id,
            "employee_id": self.employee_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "normal_minutes_per_week": self.normal_minutes_per_week,
            "normal_weeks_in_month": self.normal_weeks_in_month,
            "normal_overtime_multiplier": self.normal_overtime_multiplier,
            "attendance": self.attendance.to_dict(include_relationships=True)
            if include_relationships and self.attendance else None,
            "employee": self.employee.to_dict(include_relationships=False)
            if include_relationships and self.employee else None,
            "payslip": self.payslip.to_dict(include_relationships=False)
            if include_relationships and self.payslip else None
        }


class DeductionsORM(Base):
    __tablename__ = "applied_deductions"
    deduction_id: str = Column(String(ID_LEN), primary_key=True)
    payslip_id: str = Column(String(ID_LEN), ForeignKey('payslip.payslip_id'))
    amount_in_cents: int = Column(Integer)
    reason: str = Column(String(255))
    payslip = relationship('PaySlipORM', back_populates='applied_deductions', uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "deduction_id": self.deduction_id,
            "payslip_id": self.payslip_id,
            "amount_in_cents": self.amount_in_cents,
            "reason": self.reason

        }


class BonusPayORM(Base):
    __tablename__ = "bonus_pay"
    bonus_id: str = Column(String(ID_LEN), primary_key=True)
    payslip_id: str = Column(String(ID_LEN), ForeignKey('payslip.payslip_id'))
    amount_in_cents: int = Column(Integer)
    reason: str = Column(String(255))
    payslip = relationship('PaySlipORM', back_populates='bonus_pay', uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "bonus_id": self.bonus_id,
            "payslip_id": self.payslip_id,
            "amount_in_cents": self.amount_in_cents,
            "reason": self.reason,
        }


class PaySlipORM(Base):
    __tablename__ = 'payslip'
    payslip_id: str = Column(String(ID_LEN), primary_key=True)
    employee_id: str = Column(String(ID_LEN), ForeignKey('employee.employee_id'))
    salary_id: str = Column(String(ID_LEN), ForeignKey('salaries.salary_id'))

    pay_period_start: date = Column(Date, index=True)
    pay_period_end: date = Column(Date, index=True)

    employee = relationship('EmployeeORM', back_populates='payslip', lazy=True, uselist=False)
    salary = relationship('SalaryORM', back_populates="payslip", lazy=True, uselist=False)

    applied_deductions = relationship('DeductionsORM', back_populates="payslip", lazy=True,
                                      cascade="all, delete-orphan", uselist=True)
    bonus_pay = relationship('BonusPayORM', back_populates='payslip', lazy=True,
                             cascade='all, delete-orphan', uselist=True)

    work_sheet = relationship('WorkSummaryORM', back_populates='payslip', lazy=True,
                              uselist=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    # noinspection PyUnresolvedReferences
    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self, include_relationships: bool = False):
        return {
            "payslip_id": self.payslip_id,
            "employee_id": self.employee_id,
            "salary_id": self.salary_id,
            "pay_period_start": self.pay_period_start.isoformat() if self.pay_period_start else None,
            "pay_period_end": self.pay_period_end.isoformat() if self.pay_period_end else None,
            "employee": self.employee.to_dict(
                include_relationships=False) if self.employee and include_relationships else None,
            "salary": self.salary.to_dict(include_relationships=False) if self.salary else None,
            "applied_deductions": [deduction.to_dict() for deduction in
                                   self.applied_deductions] if self.applied_deductions else [],
            "bonus_pay": [bonus.to_dict() for bonus in self.bonus_pay] if self.bonus_pay else [],
            "work_sheet": self.work_sheet.to_dict(
                include_relationships=True) if self.work_sheet and include_relationships else None,
        }
