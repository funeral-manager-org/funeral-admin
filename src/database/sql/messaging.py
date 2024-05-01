from sqlalchemy import Column, String, inspect, Integer, Boolean, Text

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class SMSInboxORM(Base):
    __tablename__ = "sms_inbox"

    to_branch: str = Column(String(ID_LEN))
    message_id: str = Column(String(ID_LEN), primary_key=True)
    is_response: bool = Column(Boolean)
    parent_messaged_id: str = Column(String(ID_LEN), nullable=True)
    message: str = Column(Text)
    date_time_received: str = Column(String(36))
    is_read: bool = Column(Boolean)

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
            "to_branch": self.to_branch,
            "message_id": self.message_id,
            "is_response": self.is_response,
            "parent_message_id": self.parent_messaged_id,
            "message": self.message,
            "date_time_received": self.date_time_received,
            "is_read": self.is_read
        }


class SMSComposeORM(Base):
    __tablename__ = "sms_compose"

    message_id: str = Column(String(ID_LEN), primary_key=True)
    message: str = Column(Text)
    to_branch: str = Column(String(ID_LEN))
    recipient_type: str = Column(String(36))
    date_time_composed: str = Column(String(36))
    date_time_sent: str = Column(String(36))
    is_delivered: bool = Column(Boolean)

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
            "message_id": self.message_id,
            "message": self.message,
            "to_branch": self.to_branch,
            "recipient_type": self.recipient_type,
            "date_time_composed": self.date_time_composed,
            "date_time_sent": self.date_time_sent,
            "is_delivered": self.is_delivered
        }
