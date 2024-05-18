from sqlalchemy import Column, String, inspect, Integer, Boolean, Text

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class SubscriptionsORM(Base):
    __tablename__ = "subscriptions"
    company_id: str = Column(String(ID_LEN), primary_key=True)
    plan_name: str = Column(String(NAME_LEN))
    total_sms: int = Column(Integer)
    total_emails: int = Column(Integer)
    total_clients: int = Column(Integer)
    date_subscribed: str = Column(Integer)
    subscription_amount: int = Column(Integer)
    subscription_period: int = Column(Integer)

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
            "plan_name": self.plan_name,
            "total_sms": self.total_sms,
            "total_emails": self.total_emails,
            "total_clients": self.total_clients,
            "date_subscribed": self.date_subscribed,
            "subscription_amount": self.subscription_amount,
            "subscription_period": self.subscription_period
        }


class SMSPackageORM(Base):
    __tablename__ = "sms_package"
    package_id: str = Column(String(ID_LEN), primary_key=True)
    company_id: str = Column(String(ID_LEN))
    package_name: str = Column(String(NAME_LEN))
    total_sms: int = Column(Integer)
    is_paid: bool = Column(Boolean)
    is_added: bool = Column(Boolean)
    date_bought: str = Column(String(36))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def use_package(self) -> int:
        if self.is_paid and not self.is_added:
            remaining = self.total_sms
            self.total_sms = 0
            self.is_added = True
            return remaining
        return 0

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        return {
            'package_id': self.package_id,
            'company_id': self.company_id,
            'package_name': self.package_name,
            'total_sms': self.total_sms,
            'is_paid': self.is_paid,
            'is_added': self.is_added,
            'date_bought': self.date_bought
        }