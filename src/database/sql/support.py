
from datetime import date

from sqlalchemy import Column, String, inspect, Integer, Boolean, Date, ForeignKey, Sequence
from sqlalchemy.orm import relationship

from src.database.constants import ID_LEN


class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref=backref("tickets_created", lazy="dynamic"))
    assignee = relationship("User", foreign_keys=[assigned_to], backref=backref("tickets_assigned", lazy="dynamic"))
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
