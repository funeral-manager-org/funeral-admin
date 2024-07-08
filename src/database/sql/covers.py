from datetime import date

from sqlalchemy import Column, String, inspect, Integer, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class ClientPersonalInformationORM(Base):
    __tablename__ = "client_personal_information"
    uid = Column(String(ID_LEN), primary_key=True)
    branch_id = Column(String(ID_LEN))
    company_id = Column(String(ID_LEN))
    title = Column(String(NAME_LEN))
    full_names = Column(String(NAME_LEN))
    surname = Column(String(NAME_LEN))

    id_number = Column(String(20))
    date_of_birth = Column(String(10))
    nationality = Column(String(NAME_LEN))

    insured_party = Column(String(36))
    relation_to_policy_holder = Column(String(30))
    plan_number = Column(String(9))
    policy_number = Column(String(9))

    address_id = Column(String(ID_LEN), nullable=True)
    contact_id = Column(String(ID_LEN), nullable=True)
    postal_id = Column(String(ID_LEN), nullable=True)
    bank_account_id = Column(String(ID_LEN), nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        _dict = {
            "uid": self.uid,
            "branch_id": self.branch_id,
            "company_id": self.company_id,
            "title": self.title,
            "full_names": self.full_names,
            "surname": self.surname,
            "id_number": self.id_number,
            "date_of_birth": self.date_of_birth,
            "nationality": self.nationality,
            "insured_party": self.insured_party,
            "relation_to_policy_holder": self.relation_to_policy_holder,
            "plan_number": self.plan_number,
            "policy_number": self.policy_number,
            "address_id": self.address_id,
            "contact_id": self.contact_id,
            "postal_id": self.postal_id,
            "bank_account_id": self.bank_account_id
        }
        return _dict


class ClaimsORM(Base):
    __tablename__ = "claims"

    uid = Column(String(ID_LEN))
    claim_number = Column(String(9), primary_key=True)
    branch_uid = Column(String(ID_LEN))
    company_uid = Column(String(ID_LEN))

    employee_id = Column(String(ID_LEN), nullable=True)
    plan_number = Column(String(9))
    policy_number = Column(String(9))

    claim_amount = Column(Integer)
    claim_total_paid = Column(Integer)
    claimed_for_uid = Column(String(ID_LEN), nullable=True)

    date_paid = Column(String(10))
    claim_status = Column(String(36))
    funeral_company = Column(String(255))
    claim_type = Column(String(36))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

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
            "branch_uid": self.branch_uid,
            "company_uid": self.company_uid,
            "claim_number": self.claim_number,
            "plan_number": self.plan_number,
            "policy_number": self.policy_number,
            "claim_amount": self.claim_amount,
            "claim_total_paid": self.claim_total_paid,
            "claimed_for_uid": self.claimed_for_uid,
            "date_paid": self.date_paid,
            "claim_status": self.claim_status,
            "funeral_company": self.funeral_company,
            "claim_type": self.claim_type
        }


class PolicyRegistrationDataORM(Base):
    __tablename__ = "policy_registration_data"
    uid = Column(String(ID_LEN), primary_key=True)
    branch_id = Column(String(ID_LEN))
    company_id = Column(String(ID_LEN))

    policy_number = Column(String(9), unique=True)
    plan_number = Column(String(9))
    policy_type = Column(String(255))  # This is assuming policy_type is a string, adjust if it's another type

    total_family_members = Column(Integer)
    total_premiums = Column(Integer)
    payment_code_reference = Column(String(9))
    date_activated = Column(String(10))
    first_premium_date = Column(String(10))
    payment_day = Column(Integer)
    client_signature = Column(String(255))
    employee_signature = Column(String(255))

    payment_method = Column(String(255))

    policy_active = Column(Boolean, default=False)
    premiums = relationship('PremiumsORM', backref="policy_data", lazy=True, cascade="all, delete-orphan")

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        result = {
            "uid": self.uid,
            "branch_id": self.branch_id,
            "company_id": self.company_id,
            "policy_number": self.policy_number,
            "plan_number": self.plan_number,
            "policy_type": self.policy_type,
            "total_family_members": self.total_family_members,
            "total_premiums": self.total_premiums,
            "payment_code_reference": self.payment_code_reference,
            "date_activated": self.date_activated,
            "first_premium_date": self.first_premium_date,
            "payment_day": self.payment_day,
            "client_signature": self.client_signature,
            "employee_signature": self.employee_signature,
            "payment_method": self.payment_method,
            "policy_active": self.policy_active
        }
        if self.premiums:
            result.update(premiums=[premium.to_dict() for premium in self.premiums])
        return result


class PremiumsORM(Base):
    __tablename__ = "premiums"
    premium_id: str = Column(String(ID_LEN), primary_key=True)
    policy_number: str = Column(String(9), ForeignKey('policy_registration_data.policy_number'))
    scheduled_payment_date: date = Column(Date)

    payment_amount: int = Column(Integer)
    amount_paid: int = Column(Integer)
    date_paid: date = Column(Date)

    payment_method: str = Column(String(36))

    payment_status: str = Column(String(36))

    next_payment_amount: int = Column(Integer)
    next_payment_date: date = Column(Date)

    payment_frequency: str = Column(String(36))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            "premium_id": self.premium_id,
            "policy_number": self.policy_number,
            "scheduled_payment_date": self.scheduled_payment_date,

            "payment_amount": self.payment_amount,
            "amount_paid": self.amount_paid,
            "date_paid": self.date_paid,

            "payment_method": self.payment_method,
            "payment_status": self.payment_status,

            "next_payment_amount": self.next_payment_amount,
            "next_payment_date": self.next_payment_date,
            "payment_frequency": self.payment_frequency,
        }
