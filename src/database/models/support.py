from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from database.models.users import User
from src.utils import create_id


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketMessage(BaseModel):
    message_id: str = Field(default_factory=create_id)
    ticket_id: str
    sender_id: str
    message: str
    created_at: datetime = Field(default=datetime.utcnow)
    sender: User


class Ticket(BaseModel):
    ticket_id: str = Field(default_factory=create_id)
    subject: str
    message: str
    status: str = Field(default=TicketStatus.OPEN.value)
    priority: str = Field(default=TicketPriority.MEDIUM.value)
    created_at: datetime = Field(default=datetime.utcnow)
    updated_at: datetime = Field(default=datetime.utcnow)
    user_id: str
    assigned_to: str

    user: User
    assignee: User
    messages: list[TicketMessage]
