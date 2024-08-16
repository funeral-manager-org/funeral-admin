from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.utils import create_id


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

    @classmethod
    def UN_RESOLVED(cls) -> list[str]:
        return [cls.OPEN.value, cls.IN_PROGRESS.value]


class TicketTypes(str, Enum):
    BILLING = "billing"
    COVERS = "covers"
    MESSAGING = "messaging"
    EMPLOYEES = "employees"
    PLANS = "plans"

    @classmethod
    def ticket_types_list(cls) -> list[str]:
        return [cls.BILLING.value, cls.COVERS.value, cls.MESSAGING.value, cls.EMPLOYEES.value, cls.PLANS.value]


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    @classmethod
    def priority_list(cls) -> list[str]:
        """

        :return:
        """
        return [cls.LOW.value, cls.MEDIUM.value, cls.HIGH.value, cls.URGENT.value]


def create_ticket_id() -> str:
    return create_id()


class TicketMessage(BaseModel):
    message_id: str = Field(default_factory=create_id)
    ticket_id: str
    sender_id: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Ticket(BaseModel):
    ticket_id: str

    user_id: str

    assigned_to: str | None = Field(default=None)
    ticket_type: str
    subject: str

    status: str = Field(default=TicketStatus.OPEN.value)
    priority: str = Field(default=TicketPriority.MEDIUM.value)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    messages: list[TicketMessage]

    @property
    def sorted_messages(self):
        return sorted(self.messages, key=lambda msg: msg.created_at) if self.messages else []


class NewTicketForm(BaseModel):
    ticket_type: str
    subject: str
    priority: str
    message: str
