from sqlalchemy import Column, String, Date, Boolean, Integer, inspect, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from src.database.constants import ID_LEN
from src.database.sql import engine

Base = declarative_base()


class PaymentORM(Base):
    __tablename__ = 'payments'

    transaction_id = Column(String(ID_LEN), primary_key=True)
    subscription_id = Column(String(ID_LEN), ForeignKey('subscriptions.subscription_id'))
    package_id = Column(String(ID_LEN), ForeignKey('sms_package.package_id'))
    invoice_number = Column(Integer, Sequence('invoice_number_seq'), autoincrement=True)
    amount_paid = Column(Integer)
    date_paid = Column(Date)
    payment_method = Column(String(32))
    is_successful = Column(Boolean, default=False)
    month = Column(Integer)
    comments = Column(String(255))

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
