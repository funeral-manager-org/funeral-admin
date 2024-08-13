from datetime import date, datetime

from sqlalchemy import Column, String, Text, DateTime, inspect, Integer, Boolean, Date, ForeignKey, Sequence
from sqlalchemy.orm import relationship, backref

from src.database.sql import Base, engine
from src.database.constants import ID_LEN, NAME_LEN


class TicketMessageORM(Base):
    """
        message_id: str = the unique identifier id for each message
        ticket_id: str = the unique identifier for the ticket the message belongs to
        sender_id: str = the unique identifier for the user who sent this message
        message: actual message sent
        created_at: date and time the message was sent
    """
    __tablename__ = "ticket_message"
    message_id: str = Column(String(ID_LEN), primary_key=True, index=True)
    ticket_id: str = Column(String(ID_LEN),  ForeignKey('tickets.ticket_id'), index=True)
    sender_id: str = Column(String(ID_LEN), index=True)
    message: str = Column(Text)
    created_at: datetime = Column(DateTime)
    ticket = relationship("TicketORM", back_populates="messages")

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
            'message_id': self.message_id,
            'ticket_id': self.ticket_id,
            'sender_id': self.sender_id,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TicketORM(Base):
    """
        ticket_id: the unique identifier for the ticket
        user_id: the id of the user who created the ticket
        assigned_to: the staff member the ticket is assigned to, this is the person who will resolve the issue
        subject: subject of the ticket
        status: status of the ticket
        priority: priority level of the ticket
        created_at: the date and time the ticket is created
        updated_at : the date and time the ticket was updated
        messages : the messages relating to this ticket
    """
    __tablename__ = 'tickets'
    ticket_id = Column(String(ID_LEN), primary_key=True, index=True)

    # the user id of the person who created the ticket
    user_id = Column(String(ID_LEN), nullable=False, index=True)

    # assigned_to is usually me the owner of the application
    assigned_to = Column(String(ID_LEN), nullable=True, index=True)
    ticket_type = Column(String(36))

    subject = Column(String(NAME_LEN), nullable=False)
    status = Column(String(36), nullable=False)
    priority = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # messages related to this ticket
    messages = relationship("TicketMessageORM", back_populates="ticket", cascade="all, delete-orphan")

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
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'assigned_to': self.assigned_to,
            'ticket_type': self.ticket_type,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'messages': [message_orm.to_dict() for message_orm in self.messages or []
                         if isinstance(message_orm, TicketMessageORM)]
        }
