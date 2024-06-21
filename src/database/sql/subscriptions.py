import datetime
from datetime import date

from sqlalchemy import Column, String, inspect, Integer, Boolean, Text, Date, ForeignKey, Sequence, DateTime
from sqlalchemy.orm import relationship

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class PaymentORM(Base):
    __tablename__ = 'payments_orm'

    transaction_id = Column(String(ID_LEN), primary_key=True)
    invoice_number = Column(Integer, Sequence('invoice_number_seq'), autoincrement=True)
    subscription_id = Column(String(ID_LEN), ForeignKey('subscriptions.subscription_id'))
    package_id = Column(String(ID_LEN), ForeignKey('packages.package_id'))

    amount_paid = Column(Integer)
    date_paid = Column(Date)
    payment_method = Column(String(32))
    is_successful = Column(Boolean, default=False)
    month = Column(Integer)
    comments = Column(String(255))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'subscription_id': self.subscription_id,
            'package_id': self.package_id,
            'invoice_number': self.invoice_number,
            'amount_paid': self.amount_paid,
            'date_paid': self.date_paid,
            'payment_method': self.payment_method,
            'is_successful': self.is_successful,
            'month': self.month,
            'comments': self.comments
        }


class SubscriptionsORM(Base):
    __tablename__ = 'subscriptions'
    subscription_id: str = Column(String(ID_LEN), primary_key=True)
    company_id: str = Column(String(ID_LEN), index=True)
    plan_name: str = Column(String(NAME_LEN))
    total_sms: int = Column(Integer)
    total_emails: int = Column(Integer)
    total_clients: int = Column(Integer)
    date_subscribed: date = Column(Date)
    subscription_amount: int = Column(Integer)
    subscription_period: int = Column(Integer)
    payments = relationship('PaymentORM', backref="subscription")

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
            "company_id": self.company_id,
            "subscription_id": self.subscription_id,
            "plan_name": self.plan_name,
            "total_sms": self.total_sms,
            "total_emails": self.total_emails,
            "total_clients": self.total_clients,
            "date_subscribed": self.date_subscribed.strftime('%Y-%m-%d') if self.date_subscribed else None,
            "subscription_amount": self.subscription_amount,
            "subscription_period": self.subscription_period
        }
        _dict.update(payments=self.payments)

        return _dict


class PackageORM(Base):
    """
        will either be an email package or an sms package
    """
    __tablename__ = "packages"
    package_id: str = Column(String(ID_LEN), primary_key=True)
    company_id: str = Column(String(ID_LEN))
    package_name: str = Column(String(NAME_LEN))
    total_sms: int = Column(Integer, default=0)
    total_email: int = Column(Integer, default=0)
    is_paid: bool = Column(Boolean)
    is_added: bool = Column(Boolean)
    date_bought: str = Column(String(36))
    payments = relationship('PaymentORM', backref="sms_packages")

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def use_package(self) -> tuple[int, int]:
        if self.is_paid and not self.is_added:
            sms_balance = self.total_sms
            email_balance = self.total_email
            self.total_sms = 0
            self.total_email = 0
            self.is_added = True
            return sms_balance, email_balance
        return 0

    def to_dict(self):
        """
        Convert the object to a dictionary representation.
        """
        _dict = {
            'package_id': self.package_id,
            'company_id': self.company_id,
            'package_name': self.package_name,
            'total_sms': self.total_sms,
            'total_email': self.total_email,
            'is_paid': self.is_paid,
            'is_added': self.is_added,
            'date_bought': self.date_bought
        }

        _dict.update(payments=self.payments)

        return _dict

#
# class EmailPackageORM(Base):
#     __tablename__ = "email_package"
#     email_package_id: str
#     company_id: str
#     package_name: str
#     total_emails: int
#     is_paid: bool
#     is_added: bool
#     date_bought: str
#     payments = relationship('PaymentORM', backref='email_packages')
#
#
# class SMSPackageORM(Base):
#     __tablename__ = 'sms_packages'
#     package_id: str = Column(String(ID_LEN), primary_key=True)
#     company_id: str = Column(String(ID_LEN))
#     package_name: str = Column(String(NAME_LEN))
#     total_sms: int = Column(Integer)
#     is_paid: bool = Column(Boolean)
#     is_added: bool = Column(Boolean)
#     date_bought: str = Column(String(36))
#     payments = relationship('PaymentORM', backref="sms_packages")
#
#     @classmethod
#     def create_if_not_table(cls):
#         if not inspect(engine).has_table(cls.__tablename__):
#             cls.__table__.create(bind=engine)
#
#     @classmethod
#     def delete_table(cls):
#         if inspect(engine).has_table(cls.__tablename__):
#             cls.__table__.drop(bind=engine)
#
#     def use_package(self) -> int:
#         if self.is_paid and not self.is_added:
#             remaining = self.total_sms
#             self.total_sms = 0
#             self.is_added = True
#             return remaining
#         return 0
#
#     def to_dict(self):
#         """
#         Convert the object to a dictionary representation.
#         """
#         _dict = {
#             'package_id': self.package_id,
#             'company_id': self.company_id,
#             'package_name': self.package_name,
#             'total_sms': self.total_sms,
#             'is_paid': self.is_paid,
#             'is_added': self.is_added,
#             'date_bought': self.date_bought,
#
#         }
#
#         _dict.update(payments=self.payments)
#
#         return _dict


class SubscriptionStatusORM(Base):
    __tablename__ = 'subscription_status'
    id = Column(String(ID_LEN), primary_key=True)
    last_checked: date = Column(Date, nullable=True)

    def to_dict(self) -> dict[str, date]:
        return {"last_checked": self.last_checked, 'id': self.id}

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)


class PaymentNoticeIntervalORM(Base):
    """
        payment notifications may be sent in an upredictable fashion this will prevent this
    """
    __tablename__ = "payment_notice_intervals"
    company_id: str = Column(String(ID_LEN), primary_key=True)
    last_payment_notice_sent_date: date = Column(Date)
    last_expired_notice_sent_date: date = Column(Date)

    def to_dict(self) -> dict[str, date]:
        return {"last_payment_notice_sent_date": self.last_payment_notice_sent_date,
                "last_expired_notice_sent_date": self.last_expired_notice_sent_date,
                'company_id': self.company_id}

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            cls.__table__.create(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)
