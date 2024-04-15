import uuid
from datetime import datetime, timedelta, date

from sqlalchemy import Column, String, inspect, ForeignKey, Boolean, func, Integer, Date, DateTime

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class GameAuthORM(Base):
    __tablename__ = 'game_auth'
    game_id: str = Column(String(ID_LEN), primary_key=True)
    game_email: str = Column(String(ID_LEN))
    game_password: str = Column(String(NAME_LEN))
    game_pin: str | None = Column(String(ID_LEN))

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
            'game_id': self.game_id,
            'game_email': self.game_email,
            'game_password': self.game_password,
            'game_pin': self.game_pin
        }


class GameIDSORM(Base):
    __tablename__ = "game_accounts"
    uid: str = Column(String(ID_LEN))
    game_id: str = Column(String(ID_LEN), primary_key=True)
    game_uid: str = Column(String(ID_LEN))
    account_type: str = Column(String(12))
    base_level: int = Column(Integer)
    state: int = Column(Integer)
    base_name: str = Column(String(NAME_LEN))
    power: int = Column(Integer)
    last_login_time: datetime = Column(DateTime)

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
            'uid': self.uid,
            'game_id': self.game_id,
            'game_uid': self.game_uid,
            'account_type': self.account_type,
            'base_level': self.base_level,
            'state': self.state,
            'base_name': self.base_name,
            'power': self.power,
            'last_login_time': self.last_login_time
        }


class GiftCodesORM(Base):
    __tablename__ = "gift_codes"
    code = Column(String(NAME_LEN), primary_key=True)
    date_submitted = Column(Date, default=func.now())
    number_days_valid = Column(Integer)

    @property
    def is_valid(self):
        if self.date_submitted is None:
            return False
        today = datetime.now().date()
        expiry_date = self.date_submitted + timedelta(days=self.number_days_valid)
        return today <= expiry_date

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
            'code': self.code,
            'date_submitted': self.date_submitted,
            'number_days_valid': self.number_days_valid,
            'is_valid': self.is_valid
        }


# noinspection PyRedeclaration
class RedeemCodesORM(Base):
    __tablename__ = "redeem_codes"

    id = Column(String(ID_LEN), primary_key=True, default=str(uuid.uuid4()))
    game_id = Column(String(ID_LEN))
    code = Column(String(NAME_LEN))

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
            'id': self.id,
            'game_id': self.game_id,
            'code': self.code
        }


class GiftCodesSubscriptionORM(Base):
    __tablename__ = "gift_codes_subscription"
    uid: str = Column(String(NAME_LEN))
    subscription_id: str = Column(String(NAME_LEN), primary_key=True)
    base_limit: int = Column(Integer)
    amount_paid: int = Column(Integer)
    remaining_codes: int = Column(Integer)
    date_created: date = Column(DateTime)
    subscription_active: bool = Column(Boolean)

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
            'uid': self.uid,
            'subscription_id': self.subscription_id,
            'base_limit': self.base_limit,
            'amount_paid': self.amount_paid,
            'remaining_codes': self.remaining_codes,
            'date_created': self.date_created if self.date_created else None,
            "subscription_active": self.subscription_active
        }
