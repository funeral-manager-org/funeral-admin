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
        }


class SMSPackageORM(Base):
    package_id: str = Column(String)
    company_id: str
    package_name: str
    total_sms: int
    is_paid: bool = Field(default=False)
    is_added: bool = Field(default=False)
    date_bought: str = Field(default_factory=date_time)
