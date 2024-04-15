import uuid
from datetime import datetime, timedelta, date

from sqlalchemy import Column, String, inspect, ForeignKey, Boolean, func, Integer, Date, DateTime

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class EmailServiceORM(Base):
    __tablename__ = 'email_service'
    subscription_id: str = Column(String(NAME_LEN), primary_key=True)
    uid: str = Column(String(NAME_LEN))
    email: str = Column(String(255))
    email_stub: str = Column(String(255))
    subscription_term: int = Column(Integer)
    total_emails: int = Column(Integer)
    subscription_active: bool = Column(Boolean)
    subscription_running: bool = Column(Boolean)


    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            'subscription_id': self.subscription_id,
            'uid': self.uid,
            'email': self.email,
            'email_stub': self.email_stub,
            'subscription_term': self.subscription_term,
            'total_emails': self.total_emails,
            'subscription_active': self.subscription_active,
            'subscription_running': self.subscription_running
        }


class EmailSubscriptionsORM(Base):
    __tablename__ = "email_subscription"
    subscription_id: str = Column(String(NAME_LEN))
    email_address: str = Column(String(255), primary_key=True)
    map_to: str = Column(String(255))
    is_used: bool = Column(Boolean)
    date_used: date = Column(Date, nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "subscription_id": self.subscription_id,
            "email_address": self.email_address,
            "map_to": self.map_to,
            "is_used": self.is_used,
            "date_used": self.date_used if self.date_used else None
        }
