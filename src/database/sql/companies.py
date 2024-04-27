from sqlalchemy import Column, String, inspect, Integer, Boolean, JSON, Date, Text

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
            Base.metadata.create_all(bind=engine)

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
    branch_id = Column(String(ID_LEN), primary_key=True)
    company_id = Column(String(ID_LEN))
    branch_name = Column(String(NAME_LEN))
    branch_description = Column(String(255))
    date_registered = Column(String(10), default=string_today)
    total_clients = Column(Integer, default=0)
    total_employees = Column(Integer, default=1)
    address_id = Column(String(ID_LEN), nullable=True)
    contact_id = Column(String(ID_LEN), nullable=True)
    postal_id = Column(String(ID_LEN), nullable=True)
    bank_account_id = Column(String(ID_LEN), nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

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

    company_id = Column(String(NAME_LEN))

    plan_number = Column(String(10), primary_key=True)
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
            Base.metadata.create_all(bind=engine)

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
    __tablename__ = "employee"
    employee_id = Column(String(9), primary_key=True)
    company_id = Column(String(ID_LEN))
    branch_id = Column(String(ID_LEN))
    uid = Column(String(ID_LEN))
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

    address_id = Column(String(ID_LEN), nullable=True)
    contact_id = Column(String(ID_LEN), nullable=True)
    postal_id = Column(String(ID_LEN), nullable=True)
    bank_account_id = Column(String(ID_LEN), nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
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
            "bank_account_id": self.bank_account_id
        }


class SalaryORM(Base):
    __tablename__ = 'salaries'

    salary_id = Column(Integer, primary_key=True)
    employee_id = Column(String(ID_LEN))
    amount = Column(Integer)
    effective_date = Column(Date)
    company_id = Column(String(ID_LEN))
    branch_id = Column(String(ID_LEN))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            'salary_id': self.salary_id,
            'employee_id': self.employee_id,
            'amount': self.amount,
            'effective_date': str(self.effective_date),
            'company_id': self.company_id,
            'branch_id': self.branch_id
        }


class SalaryPaymentORM(Base):
    __tablename__ = 'salary_payments'

    payment_id = Column(String(ID_LEN), primary_key=True)
    salary_id = Column(String(ID_LEN))
    payment_date = Column(Date)
    amount_paid = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

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
