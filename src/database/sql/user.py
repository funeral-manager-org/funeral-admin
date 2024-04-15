from sqlalchemy import Column, String, Boolean, ForeignKey, inspect, Integer

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class UserORM(Base):
    """
    User Model
        User ORM
    """
    __tablename__ = 'users'
    uid: str = Column(String(ID_LEN), primary_key=True, unique=True)
    username: str = Column(String(NAME_LEN))
    password_hash: str = Column(String(255))
    email: str = Column(String(256))
    account_verified: bool = Column(Boolean, default=False)
    is_system_admin: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def __init__(self,
                 uid: str,
                 username: str,
                 password_hash: str,
                 email: str,
                 account_verified: bool = False,
                 is_system_admin: bool = False
                 ):
        self.uid = uid
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.account_verified = account_verified
        self.is_system_admin = is_system_admin

    def __bool__(self) -> bool:
        return bool(self.uid) and bool(self.username) and bool(self.email)

    def to_dict(self) -> dict[str, str | bool]:
        return {
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'account_verified': self.account_verified,
            'is_system_admin': self.is_system_admin
        }


class ProfileORM(Base):
    """
        Profile ORM
    """
    __tablename__ = "profile"
    uid: str = Column(String(ID_LEN))
    main_game_id: str = Column(String(ID_LEN), primary_key=True)
    profile_name: str = Column(String(12))
    notes: str = Column(String(254))
    currency: str = Column(String(6))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self) -> dict[str, str | int]:
        """
        Convert the ProfileORM instance to a dictionary.
        :return: Dictionary representing the ProfileORM instance.
        """
        return {
            'uid': self.uid,
            'main_game_id': self.main_game_id,
            'profile_name': self.profile_name,
            'notes': self.notes,
            'currency': self.currency
        }

    def __eq__(self, other):
        if not isinstance(other, ProfileORM):
            return False
        return (self.game_id == other.game_id) and (self.uid == self.uid)


class PayPalORM(Base):
    __tablename__ = 'paypal_account'
    uid = Column(String(NAME_LEN), primary_key=True)
    paypal_email: str = Column(String(NAME_LEN))


    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self) -> dict[str, str]:
        return {
            'uid': self.uid,
            'paypal_email': self.paypal_email
        }
